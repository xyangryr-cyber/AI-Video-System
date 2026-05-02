"""Tests for [SPEC-B-006] Preferences Table and Storage Consistency.

Real assertions for AC-1..AC-6 (SPEC-12.1 / 12.2 / 12.3). Mirrors
``tests/unit/infra/test_preferences.py`` (committed in 7c24c2f) with
one test per TestAC class to match the task card's Test Mapping
(test_auto_insert_on_project_create / test_last_confirmed_at_updated /
test_snapshot_md_readonly / test_no_writeback_from_exports /
test_sqlite_backup_exists / test_no_restore_from_project_state_json).

Coverage:

* AC-1 (SPEC-12.1): creating a project auto-inserts the matching
  ``preferences`` row (SQLite is the single source of truth).
* AC-2 (SPEC-12.1): confirming preferences stamps ``last_confirmed_at``.
* AC-3 (SPEC-12.2): ``snapshot.md`` is a read-only export -- mutating
  it on disk MUST NOT feed back into what the API returns.
* AC-4 (SPEC-12.2): no code path reads ``snapshot.md`` /
  ``project_state.json`` and writes the result into the DB.
* AC-5 (SPEC-12.3): ``app.sqlite3.bak`` is produced by the backup
  helper in the same data directory as the live DB.
* AC-6 (SPEC-12.3): no code path restores the DB from
  ``project_state.json`` (canonical recovery source is ``.bak``).
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"
BACKEND_DIR = REPO_ROOT / "src" / "backend"


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    return c


def _create_project_with_prefs(conn: sqlite3.Connection, pid: str = "proj_a") -> str:
    from src.backend.db.repositories.preferences_repo import (
        PreferencesRepository,
    )

    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES (?, 'T', 'D')",
        (pid,),
    )
    conn.commit()
    PreferencesRepository(conn).initialize_for_project(pid)
    return pid


class TestAC1AutoInsertOnProjectCreate:
    """AC-1: new project creation auto-inserts the matching preferences row."""

    def test_auto_insert_on_project_create(self, conn):
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        conn.execute(
            "INSERT INTO projects(project_id, title, description) "
            "VALUES ('proj_new', 'T', 'D')"
        )
        conn.commit()

        PreferencesRepository(conn).initialize_for_project("proj_new")

        row = conn.execute(
            "SELECT * FROM preferences WHERE project_id = 'proj_new'"
        ).fetchone()
        assert row is not None, (
            "preferences row must be auto-inserted when a new project is created"
        )
        assert row["global_rules_md"] == ""
        assert row["user_preferences_md"] == ""
        assert row["project_preferences_md"] == ""
        assert row["last_confirmed_at"] is None

        PreferencesRepository(conn).initialize_for_project("proj_new")
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM preferences WHERE project_id = 'proj_new'"
        ).fetchone()["n"]
        assert count == 1


class TestAC2LastConfirmedAtUpdated:
    """AC-2: confirming preferences stamps last_confirmed_at."""

    def test_last_confirmed_at_updated(self, conn):
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        pid = _create_project_with_prefs(conn)
        repo = PreferencesRepository(conn)

        before = repo.get(pid)
        assert before["last_confirmed_at"] is None, (
            "newly initialized preferences row must start with last_confirmed_at = NULL"
        )

        repo.mark_confirmed(pid)
        after = repo.get(pid)
        stamp = after["last_confirmed_at"]
        assert stamp is not None, "mark_confirmed must stamp last_confirmed_at"
        assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", stamp), (
            f"last_confirmed_at must be ISO-8601 UTC, got {stamp!r}"
        )


class TestAC3SnapshotMdReadonly:
    """AC-3: modifying snapshot.md must not change API return value."""

    def test_snapshot_md_readonly(self, conn, tmp_path):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from src.backend.api.routes.preferences import get_db, router
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        pid = _create_project_with_prefs(conn)
        repo = PreferencesRepository(conn)
        repo.update(
            pid,
            global_rules_md="db-global",
            user_preferences_md="db-user",
            project_preferences_md="db-project",
        )

        snap = tmp_path / "snapshot.md"
        snap.write_text(
            "# tampered export -- must not be read back\nglobal_rules_md: hacked\n",
            encoding="utf-8",
        )

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: conn
        app.include_router(router)
        client = TestClient(app)

        body = client.get(f"/api/projects/{pid}/preferences").json()
        assert body["global_rules_md"] == "db-global", (
            "API must ignore snapshot.md and read from SQLite"
        )
        assert body["user_preferences_md"] == "db-user"
        assert body["project_preferences_md"] == "db-project"

        snap.write_text("hacked again", encoding="utf-8")
        body2 = client.get(f"/api/projects/{pid}/preferences").json()
        assert body2["global_rules_md"] == "db-global"


class TestAC4NoWritebackFromExports:
    """AC-4: no backend code reads snapshot.md / project_state.json and writes DB."""

    def test_no_writeback_from_exports(self):
        offenders: list[tuple[str, str]] = []
        for py in BACKEND_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            for export in ("snapshot.md", "project_state.json"):
                if export not in text:
                    continue
                read_pattern = (
                    r"open\s*\([^)]*"
                    + re.escape(export)
                    + r"[^)]*['\"]r|"
                    + r"Path\([^)]*"
                    + re.escape(export)
                    + r"[^)]*\)\s*\.read_text"
                )
                reads_file = bool(re.search(read_pattern, text))
                if export == "project_state.json":
                    reads_file = reads_file or bool(re.search(r"json\.load\s*\(", text))
                writes_db = bool(
                    re.search(
                        r"INSERT\s+INTO|UPDATE\s+\w+\s+SET",
                        text,
                        re.IGNORECASE,
                    )
                )
                if reads_file and writes_db:
                    offenders.append((str(py.relative_to(REPO_ROOT)), export))
        assert not offenders, (
            f"exports are read-only views; no backend module may read "
            f"them AND issue a DB write: {offenders}"
        )


class TestAC5SqliteBackupExists:
    """AC-5: backup helper produces app.sqlite3.bak in the data directory."""

    def test_sqlite_backup_exists(self, tmp_path):
        from src.backend.core.backup import create_sqlite_backup

        src = tmp_path / "app.sqlite3"
        c = sqlite3.connect(str(src))
        c.execute("CREATE TABLE t(x INTEGER)")
        c.execute("INSERT INTO t(x) VALUES (1)")
        c.commit()
        c.close()

        bak_path = create_sqlite_backup(src)
        assert bak_path.name == "app.sqlite3.bak"
        assert bak_path.parent == src.parent, (
            "backup must live in the same data directory as the DB"
        )
        assert bak_path.exists()
        assert bak_path.stat().st_size > 0

        c2 = sqlite3.connect(str(bak_path))
        rows = list(c2.execute("SELECT x FROM t"))
        assert rows == [(1,)]
        c2.close()


class TestAC6NoRestoreFromProjectStateJson:
    """AC-6: no code path restores DB from project_state.json (source = .bak)."""

    def test_no_restore_from_project_state_json(self):
        offenders: list[str] = []
        for py in BACKEND_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            if "project_state.json" not in text:
                continue
            code_lines = [
                ln
                for ln in text.splitlines()
                if ln.strip() and not ln.strip().startswith("#")
            ]
            joined = "\n".join(code_lines)
            if "project_state.json" not in joined:
                continue
            if re.search(
                r"(restore|recover|load)[^=\n]{0,80}project_state\.json|"
                r"project_state\.json[^=\n]{0,80}(restore|recover|load)",
                joined,
                re.IGNORECASE,
            ):
                offenders.append(str(py.relative_to(REPO_ROOT)))
        assert not offenders, (
            f"project_state.json is a read-only export; it is NOT a "
            f"recovery source. Offenders: {offenders}"
        )

        backup_src = (BACKEND_DIR / "core" / "backup.py").read_text(encoding="utf-8")
        assert "app.sqlite3.bak" in backup_src, (
            "src/backend/core/backup.py must reference app.sqlite3.bak "
            "as the canonical recovery source"
        )
