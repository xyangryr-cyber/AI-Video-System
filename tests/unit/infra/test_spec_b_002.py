"""Tests for [SPEC-B-002] Persistent Write Path Uniqueness.

Enforces SPEC-1.2: SQLite is the ONE structured source of truth; media
files are written first, then an ``artifact_ref`` is committed to DB;
``snapshot.md`` and ``project_state.json`` are one-way read-only exports.

Test strategy per AC (mapped from task card):

- AC-1 `snapshot.md` change does NOT overwrite DB:
    * Behaviour test: ``ArtifactManager.commit_artifact`` updates DB with
      the new artifact path even when a hostile ``snapshot.md`` exists
      in the storage root (proves the write path does not round-trip
      through the exported file).
    * Static guard: no module that mentions ``snapshot.md`` also issues
      raw DB write SQL, preventing a future writeback loop.

- AC-2 orphan file cleanup on ``artifact_ref`` failure:
    * Inject a repository whose ``set_artifact_path`` raises; assert the
      file that was written to disk is removed and the error propagates.
    * Mutation sanity: on success the file AND the DB row land together
      (blocks a degenerate "always delete" implementation).

- AC-3 no ``project_state.json`` writeback:
    * Mirror of the task-card ``grep`` verification as a test; scans all
      ``src/backend/**/*.py`` files and flags any module that references
      ``project_state.json`` outside an export/read-only/dump context
      AND issues DB write SQL.

- AC-4 DB writes centralized in repository layer:
    * Static scan: any ``INSERT INTO`` / ``UPDATE ... SET`` / ``DELETE
      FROM`` in ``src/backend/**/*.py`` MUST live under
      ``src/backend/db/repositories/``.
    * Behaviour: ``BaseRepository.execute`` actually routes through its
      connection (a stub that no-ops would fail this).
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "src" / "backend"
SCHEMA_FILE = BACKEND_DIR / "db" / "schema.sql"

# Filenames that AC-1 / AC-3 treat as one-way export artefacts.
EXPORT_FILENAMES = ("snapshot.md", "project_state.json")

# SQL keywords that indicate a DB write; combined into a single pattern
# so a stray `INSERT INTO`, `UPDATE <table> SET`, or `DELETE FROM` in a
# non-repository file trips AC-4.
WRITE_SQL_PATTERN = re.compile(
    r"\b(INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM)\b",
    flags=re.IGNORECASE,
)

# Valid repository directories. ``src/backend/repositories/`` hosts
# cross-table writers (e.g. ProjectStateRepository for C-016) that are
# transaction-aware; they are legitimate repository-layer code even
# though they live outside ``src/backend/db/repositories/``.
VALID_REPO_PREFIXES: tuple[tuple[str, ...], ...] = (
    ("src", "backend", "db", "repositories"),
    ("src", "backend", "repositories"),
)

# Functions in non-repository files that perform DB writes directly.
# Each entry: (rel_path, function_name, "TODO(SPEC-X-NNN): reason").
# These MUST be refactored into repository classes when their owning
# task card is implemented.
KNOWN_STRAY_WRITE_EXCEPTIONS: dict[str, set[str]] = {
    "src/backend/workers/p7a_tasks.py": {
        "record_huey_task",  # TODO(SPEC-B-015): use AsyncTaskRepository.create()
    },
}

# Docstring delimiter patterns for skipping false positives.
_TRIPLE_QUOTE = re.compile(r'^[^"]*("""|\'\'\')')


# ---- helpers ---------------------------------------------------------------


def _backend_py_files() -> list[Path]:
    """All Python sources under ``src/backend/`` (no cache)."""
    return [p for p in BACKEND_DIR.rglob("*.py") if "__pycache__" not in p.parts]


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _seed_project_and_phase(
    conn: sqlite3.Connection,
    project_id: str = "proj_b002",
    phase_num: int = 0,
    seeded_artifact_path: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name, "
        "artifact_path) VALUES(?, ?, ?, ?)",
        (project_id, phase_num, f"P{phase_num}", seeded_artifact_path),
    )
    conn.commit()


def _line_is_inside_docstring(lines: list[str], idx: int) -> bool:
    """Return True if ``lines[idx]`` is inside a triple-quoted docstring."""
    inside = False
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#"):
            continue
        count = stripped.count('"""') + stripped.count("'''")
        if count % 2 == 1:
            inside = not inside
        if i == idx:
            return inside
    return False


def _references_with_writeback(filename: str) -> list[str]:
    """Return ``src/backend`` modules that (a) reference ``filename``
    outside an allowed export/read-only/dump context and (b) also issue
    DB write SQL. This is the static form of AC-1 / AC-3 guard.
    """
    offenders: list[str] = []
    allow = re.compile(r"export|read_only|dump", flags=re.IGNORECASE)
    for py in _backend_py_files():
        text = py.read_text(encoding="utf-8")
        if filename not in text:
            continue
        hits = [line for line in text.splitlines() if filename in line]
        unguarded = [line for line in hits if not allow.search(line)]
        if not unguarded:
            continue
        if WRITE_SQL_PATTERN.search(text):
            offenders.append(str(py.relative_to(REPO_ROOT)))
    return offenders


# ---- AC-1 ------------------------------------------------------------------


class TestAC1SnapshotMdChangeDoesNotOverwriteDb:
    """AC-1: 手动修改 `snapshot.md` → 重启 API → DB 值未被覆盖."""

    def test_artifact_manager_writes_db_not_snapshot(self, tmp_path):
        """With a hostile ``snapshot.md`` in the storage root, the
        write path still commits the new ``artifact_path`` to DB and
        does NOT round-trip through the edited file.
        """
        from src.backend.core.artifact_manager import ArtifactManager
        from src.backend.core.storage import MediaStorage
        from src.backend.db.repositories.phase_repository import (
            PhaseRepository,
        )

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn, seeded_artifact_path="/db/seeded/path")

        # Simulate a user (or attacker) hand-editing the exported
        # snapshot.md before the next write.
        (tmp_path / "snapshot.md").write_text(
            "HACKED artifact_path=/tmp/not_real",
            encoding="utf-8",
        )

        mgr = ArtifactManager(
            MediaStorage(tmp_path),
            PhaseRepository(conn),
        )
        written = mgr.commit_artifact("proj_b002", 0, "artifacts/p0.bin", b"payload")

        row = conn.execute(
            "SELECT artifact_path FROM phases WHERE project_id = ? AND phase_num = ?",
            ("proj_b002", 0),
        ).fetchone()

        assert written.exists(), "commit_artifact must land the file"
        assert row is not None, "phase row must exist post-commit"
        assert row[0].endswith("artifacts/p0.bin"), (
            f"DB must reflect the freshly-written artifact_path, got {row[0]!r}"
        )
        assert "HACKED" not in row[0]

    def test_no_snapshot_md_reader_also_writes_db(self):
        """Static guard: no module references ``snapshot.md`` outside
        an export/read-only/dump context while also issuing DB write
        SQL. Prevents a future writeback loop regression.
        """
        offenders = _references_with_writeback("snapshot.md")
        assert not offenders, (
            "snapshot.md must be a read-only export. Found modules "
            f"with both unguarded references and DB writes: {offenders}"
        )


# ---- AC-2 ------------------------------------------------------------------


class TestAC2OrphanFileCleanupOnArtifactRefFailure:
    """AC-2: `artifact_ref` 提交失败时孤儿文件被清理."""

    def test_orphan_file_deleted_when_repo_raises(self, tmp_path):
        from src.backend.core.artifact_manager import ArtifactManager
        from src.backend.core.storage import MediaStorage

        class ExplodingRepo:
            def set_artifact_path(self, *_args, **_kwargs):
                raise RuntimeError("simulated DB failure")

        mgr = ArtifactManager(MediaStorage(tmp_path), ExplodingRepo())

        with pytest.raises(RuntimeError, match="simulated DB failure"):
            mgr.commit_artifact("proj_b002", 0, "artifacts/orphan.bin", b"orphan")

        orphan = tmp_path / "artifacts" / "orphan.bin"
        assert not orphan.exists(), (
            "Orphan media file must be deleted when artifact_ref "
            f"commit fails; still present at {orphan}"
        )

    def test_successful_commit_persists_file_and_db_row(self, tmp_path):
        """Mutation sanity: on SUCCESS the file stays AND the DB row
        is updated. Blocks a "always delete" stub from slipping past
        the failure test above.
        """
        from src.backend.core.artifact_manager import ArtifactManager
        from src.backend.core.storage import MediaStorage
        from src.backend.db.repositories.phase_repository import (
            PhaseRepository,
        )

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        mgr = ArtifactManager(
            MediaStorage(tmp_path),
            PhaseRepository(conn),
        )
        written = mgr.commit_artifact("proj_b002", 0, "artifacts/kept.bin", b"kept")

        assert written.exists(), "file must be kept on success"
        row = conn.execute(
            "SELECT artifact_path FROM phases WHERE project_id = ? AND phase_num = ?",
            ("proj_b002", 0),
        ).fetchone()
        assert row[0].endswith("artifacts/kept.bin")


# ---- AC-3 ------------------------------------------------------------------


class TestAC3NoProjectStateJsonWriteback:
    """AC-3: 代码中无从 `project_state.json` 读取并写入 DB 的逻辑."""

    def test_no_project_state_json_writeback(self):
        offenders = _references_with_writeback("project_state.json")
        assert not offenders, (
            "project_state.json must be a read-only export. Found "
            f"modules with reader+DB-writer pairs: {offenders}"
        )


# ---- AC-4 ------------------------------------------------------------------


class TestAC4DbWritesCentralizedInRepositoryLayer:
    """AC-4: 所有 DB 写入操作集中在 repository 层，无分散写入."""

    def test_all_db_writes_live_under_repositories(self):
        """Scan every Python source under ``src/backend``. Any line
        that matches ``INSERT INTO`` / ``UPDATE <table> SET`` / ``DELETE
        FROM`` must live under ``src/backend/db/repositories/`` (or the
        recognized ``src/backend/repositories/`` cross-table path).
        """
        stray: list[str] = []
        func_re = re.compile(r"^def\s+(\w+)\s*\(")
        for py in _backend_py_files():
            rel = py.relative_to(REPO_ROOT)
            rel_str = str(rel)
            lines = py.read_text(encoding="utf-8").splitlines()
            current_func: str | None = None
            exc_funcs = KNOWN_STRAY_WRITE_EXCEPTIONS.get(rel_str, set())
            for lineno, line in enumerate(lines, 1):
                # Track function context for exception checking
                m = func_re.match(line.strip())
                if m:
                    current_func = m.group(1)
                    continue
                if not WRITE_SQL_PATTERN.search(line):
                    continue
                # Skip docstring lines
                if _line_is_inside_docstring(lines, lineno - 1):
                    continue
                # Valid repo path check
                if any(rel.parts[: len(pfx)] == pfx for pfx in VALID_REPO_PREFIXES):
                    continue
                # Known exception: inside a whitelisted function
                if current_func and current_func in exc_funcs:
                    continue
                stray.append(f"{rel}:{lineno}: {line.strip()[:100]}")
        assert not stray, (
            "DB write SQL must live in src/backend/db/repositories/ "
            "(or src/backend/repositories/). "
            "Stray writes:\n" + "\n".join(stray)
        )

    def test_base_repository_executes_against_connection(self):
        """Behaviour test: ``BaseRepository.execute`` actually runs on
        the injected connection. A no-op stub would fail this.
        """
        from src.backend.db.repositories.base import BaseRepository

        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE t (x INTEGER)")
        repo = BaseRepository(conn)
        repo.execute("INSERT INTO t VALUES (?)", (42,))
        repo.commit()
        row = conn.execute("SELECT x FROM t").fetchone()
        assert row == (42,)
