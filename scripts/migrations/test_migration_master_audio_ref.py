"""Migration-level tests for [SPEC-B-013] V006 master_audio_ref migration.

Authority:
  tasks/SPEC-B/B-013-master-audio-ref-migration.md Test Mapping AC-1..AC-3.
  docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §B-AUDP7A-1.

Strategy:
  The migration SQL file lives under scripts/migrations/ (this package) with
  a `-- ROLLBACK ----` marker separating the forward and rollback scripts.
  Tests bootstrap an in-memory SQLite DB from the v1-core baseline
  (src/backend/db/migrations/001_initial.sql), then exercise the full
  forward -> rollback -> forward sequence.

  AC-1: forward adds `master_audio_ref TEXT` + expression index on
        `json_extract(master_audio_ref, '$.based_on_phase')`.
  AC-2: rollback drops the index and the column.
  AC-3: forward -> rollback -> forward is idempotent (no errors), final
        state has the column + index back.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
MIGRATION_PATH = (
    REPO_ROOT / "scripts" / "migrations" / "V006__add_master_audio_ref.sql"
)
V1_CORE_INITIAL = (
    REPO_ROOT / "src" / "backend" / "db" / "migrations" / "001_initial.sql"
)
ROLLBACK_MARKER = "-- ROLLBACK"


def _split_forward_rollback(sql_text: str) -> tuple[str, str]:
    """Return (forward_sql, rollback_sql) split on the ROLLBACK marker."""
    lines = sql_text.splitlines()
    cut = next(
        (i for i, line in enumerate(lines)
         if line.lstrip().startswith(ROLLBACK_MARKER)),
        None,
    )
    assert cut is not None, (
        f"migration missing '{ROLLBACK_MARKER}' marker: {MIGRATION_PATH}"
    )
    return "\n".join(lines[:cut]), "\n".join(lines[cut + 1 :])


def _fresh_conn_with_baseline() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(V1_CORE_INITIAL.read_text(encoding="utf-8"))
    return conn


def _projects_columns(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    rows = conn.execute("PRAGMA table_info(projects)").fetchall()
    return {
        r[1]: {"cid": r[0], "type": r[2], "notnull": r[3],
               "default": r[4], "pk": r[5]}
        for r in rows
    }


def _index_sql(conn: sqlite3.Connection, name: str) -> str | None:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='index' AND name=?",
        (name,),
    ).fetchone()
    return row[0] if row else None


# ---------------------------------------------------------------------------


class TestAC1ForwardAddsColumnAndIndex:
    """AC-1: forward section adds column + expression index."""

    def test_forward_adds_column(self) -> None:
        assert MIGRATION_PATH.exists(), (
            f"migration file missing: {MIGRATION_PATH}"
        )
        forward, _ = _split_forward_rollback(
            MIGRATION_PATH.read_text(encoding="utf-8")
        )
        # AC-1 prescribes the literal ALTER statement.
        assert (
            "ALTER TABLE projects ADD COLUMN master_audio_ref TEXT" in forward
        ), (
            "forward section must contain the exact AC-1 ALTER statement"
        )
        conn = _fresh_conn_with_baseline()
        conn.executescript(forward)
        cols = _projects_columns(conn)
        assert "master_audio_ref" in cols, (
            f"column missing after forward; cols={list(cols)}"
        )
        assert cols["master_audio_ref"]["type"].upper() == "TEXT"
        assert cols["master_audio_ref"]["notnull"] == 0, (
            "master_audio_ref must be nullable (legacy rows have no master)"
        )

    def test_forward_creates_index(self) -> None:
        forward, _ = _split_forward_rollback(
            MIGRATION_PATH.read_text(encoding="utf-8")
        )
        assert "idx_projects_master_audio_phase" in forward
        assert "json_extract(master_audio_ref, '$.based_on_phase')" in forward
        conn = _fresh_conn_with_baseline()
        conn.executescript(forward)
        idx_sql = _index_sql(conn, "idx_projects_master_audio_phase")
        assert idx_sql is not None, (
            "idx_projects_master_audio_phase not registered"
        )
        assert (
            "json_extract(master_audio_ref, '$.based_on_phase')" in idx_sql
        ), f"index must use json_extract expression; got: {idx_sql}"


class TestAC2RollbackDropsColumnAndIndex:
    """AC-2: rollback section reverts both schema objects."""

    def test_rollback_drops_column_and_index(self) -> None:
        forward, rollback = _split_forward_rollback(
            MIGRATION_PATH.read_text(encoding="utf-8")
        )
        up = rollback.upper()
        assert "DROP INDEX" in up and "idx_projects_master_audio_phase" in rollback
        assert "DROP COLUMN" in up and "master_audio_ref" in rollback
        conn = _fresh_conn_with_baseline()
        conn.executescript(forward)
        conn.executescript(rollback)
        assert "master_audio_ref" not in _projects_columns(conn)
        assert _index_sql(conn, "idx_projects_master_audio_phase") is None


class TestAC3ForwardRollbackForwardIdempotent:
    """AC-3: forward -> rollback -> forward round-trip is clean."""

    def test_forward_rollback_forward_idempotent(self) -> None:
        forward, rollback = _split_forward_rollback(
            MIGRATION_PATH.read_text(encoding="utf-8")
        )
        conn = _fresh_conn_with_baseline()
        # Round 1: apply forward.
        conn.executescript(forward)
        assert "master_audio_ref" in _projects_columns(conn)
        # Round 2: rollback.
        conn.executescript(rollback)
        assert "master_audio_ref" not in _projects_columns(conn)
        # Round 3: forward again -- must succeed without errors.
        conn.executescript(forward)
        assert "master_audio_ref" in _projects_columns(conn)
        assert _index_sql(conn, "idx_projects_master_audio_phase") is not None
