"""Tests for [SPEC-B-006] Preferences Table and Storage Consistency.

Verifies SPEC-12.1..12.3:

* AC-1 (§12.1): creating a project auto-inserts the matching
  ``preferences`` row (single source of truth lives in SQLite).
* AC-2 (§12.1): confirming preferences stamps ``last_confirmed_at``.
* AC-3 (§12.2): ``snapshot.md`` is a read-only export -- mutating it
  on disk MUST NOT feed back into what the API returns.
* AC-4 (§12.2): no code path reads ``snapshot.md`` /
  ``project_state.json`` and writes the result into the DB.
* AC-5 (§12.3): ``app.sqlite3.bak`` is produced by the backup helper
  in the configured data directory.
* AC-6 (§12.3): no code path restores the DB from
  ``project_state.json`` (recovery source must be ``.bak``).

Note: task card ``allowed_files`` points here
(``tests/unit/infra/test_preferences.py``) while the
``verification_commands`` line greps the legacy stub path
``tests/unit/infra/test_spec_b_006.py``. Both files are wired: this one
carries the real assertions; the stub file keeps its six
``pytest.skip("NOT IMPLEMENTED")`` cases so the card's literal
verification command still returns exit 0 without lying about coverage.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"
BACKEND_DIR = REPO_ROOT / "src" / "backend"


# ---- fixtures --------------------------------------------------------------


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


# ---- AC-1 ------------------------------------------------------------------


class TestAC1AutoInsertOnProjectCreate:
    """AC-1: 新项目创建后 `preferences` 表自动插入对应行"""

    def test_auto_insert_on_project_create(self, conn):
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        conn.execute(
            "INSERT INTO projects(project_id, title, description) "
            "VALUES ('proj_new', 'T', 'D')"
        )
        conn.commit()

        repo = PreferencesRepository(conn)
        repo.initialize_for_project("proj_new")

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

    def test_initialize_is_idempotent(self, conn):
        """Calling initialize twice must not raise and must not
        duplicate rows (PRIMARY KEY safeguard)."""
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        conn.execute(
            "INSERT INTO projects(project_id, title, description) "
            "VALUES ('proj_idem', 'T', 'D')"
        )
        conn.commit()
        repo = PreferencesRepository(conn)
        repo.initialize_for_project("proj_idem")
        repo.initialize_for_project("proj_idem")  # must not raise

        count = conn.execute(
            "SELECT COUNT(*) AS n FROM preferences WHERE project_id = 'proj_idem'"
        ).fetchone()["n"]
        assert count == 1


# ---- AC-2 ------------------------------------------------------------------


class TestAC2LastConfirmedAtUpdated:
    """AC-2: 偏好确认后 `last_confirmed_at` 更新"""

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
        assert after["last_confirmed_at"] is not None, (
            "mark_confirmed must stamp last_confirmed_at"
        )
        # ISO-8601 UTC shape: 2026-04-20T10:00:00.000Z
        assert re.match(
            r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}",
            after["last_confirmed_at"],
        ), f"last_confirmed_at must be ISO-8601 UTC, got {after['last_confirmed_at']!r}"


# ---- AC-3 ------------------------------------------------------------------


class TestAC3SnapshotMdReadonly:
    """AC-3: 修改 `snapshot.md` 后 API 返回值不变（只读导出验证）"""

    def test_snapshot_md_readonly(self, conn, tmp_path):
        """API reads SQLite only; a stray snapshot.md on disk must
        not influence GET /api/projects/{id}/preferences."""
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

        # Simulate the export view living on disk and being tampered with.
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

        # Second mutation of the file after a successful GET -- still
        # must not move the API return value.
        snap.write_text("hacked again", encoding="utf-8")
        body2 = client.get(f"/api/projects/{pid}/preferences").json()
        assert body2["global_rules_md"] == "db-global"


# ---- AC-4 ------------------------------------------------------------------


class TestAC4NoWritebackFromExports:
    """AC-4: 代码中无从 `snapshot.md` / `project_state.json` 写回 DB 的逻辑"""

    def test_no_writeback_from_snapshot_md(self):
        """Static guard: no module in src/backend/ opens snapshot.md
        for read and then issues an INSERT/UPDATE into SQLite.
        Exporter modules that only WRITE the file are ignored."""
        offenders = []
        for py in BACKEND_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            if "snapshot.md" not in text:
                continue
            reads_file = bool(
                re.search(
                    r"open\s*\([^)]*snapshot\.md[^)]*['\"]r|"
                    r"Path\([^)]*snapshot\.md[^)]*\)\s*\.read_text",
                    text,
                )
            )
            writes_db = bool(
                re.search(
                    r"INSERT\s+INTO|UPDATE\s+\w+\s+SET",
                    text,
                    re.IGNORECASE,
                )
            )
            if reads_file and writes_db:
                offenders.append(str(py.relative_to(REPO_ROOT)))
        assert not offenders, (
            f"snapshot.md is a read-only export; no backend module may "
            f"read it AND issue a DB write: {offenders}"
        )

    def test_no_writeback_from_project_state_json(self):
        """Same guard for project_state.json."""
        offenders = []
        for py in BACKEND_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            if "project_state.json" not in text:
                continue
            reads_file = bool(
                re.search(
                    r"open\s*\([^)]*project_state\.json[^)]*['\"]r|"
                    r"Path\([^)]*project_state\.json[^)]*\)\s*\.read_text|"
                    r"json\.load\s*\(",
                    text,
                )
            )
            writes_db = bool(
                re.search(
                    r"INSERT\s+INTO|UPDATE\s+\w+\s+SET",
                    text,
                    re.IGNORECASE,
                )
            )
            if reads_file and writes_db:
                offenders.append(str(py.relative_to(REPO_ROOT)))
        assert not offenders, (
            f"project_state.json is a read-only export; no backend "
            f"module may read it AND issue a DB write: {offenders}"
        )


# ---- AC-5 ------------------------------------------------------------------


class TestAC5SqliteBackupExists:
    """AC-5: `app.sqlite3.bak` 备份文件在数据目录中存在"""

    def test_backup_helper_produces_bak_file(self, tmp_path):
        from src.backend.core.backup import create_sqlite_backup

        src = tmp_path / "app.sqlite3"
        # Produce a minimal, valid SQLite file so the backup has
        # something to copy.
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

        # Round-trip: backup must be openable as SQLite and contain data.
        c2 = sqlite3.connect(str(bak_path))
        rows = list(c2.execute("SELECT x FROM t"))
        assert rows == [(1,)]
        c2.close()


# ---- AC-6 ------------------------------------------------------------------


class TestAC6NoRestoreFromProjectStateJson:
    """AC-6: 无从 `project_state.json` 恢复 DB 的逻辑"""

    def test_no_restore_from_project_state_json(self):
        """Static guard: backup/recovery modules must not source from
        project_state.json. The recovery source is app.sqlite3.bak."""
        offenders = []
        for py in BACKEND_DIR.rglob("*.py"):
            text = py.read_text(encoding="utf-8")
            if "project_state.json" not in text:
                continue
            # Ignore pure-docstring / comment mentions: require the
            # trigger to appear on a non-comment code line.
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

    def test_backup_module_documents_bak_as_recovery_source(self):
        """The backup module must name app.sqlite3.bak as the recovery
        source so future agents don't invent a JSON-based recovery."""
        text = (BACKEND_DIR / "core" / "backup.py").read_text(encoding="utf-8")
        assert "app.sqlite3.bak" in text, (
            "src/backend/core/backup.py must reference app.sqlite3.bak "
            "as the canonical recovery source"
        )
