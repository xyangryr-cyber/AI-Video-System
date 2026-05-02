"""Shared test implementations for [SPEC-A-102] ProjectState v3.16 extensions.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-3 (SPEC-0A.3 扩字段).

Covers:
  - AC-1: V{NNN}__add_latest_reached_phase.sql backfills
          latest_reached_phase = current_phase for existing projects rows.
  - AC-3: ProjectState.phase_history[] entries carry `reached_at` +
          optional `completed_at` / `last_revision_at` and validate ISO
          timestamps via the pydantic PhaseHistoryEntry schema.

Re-exported by ``test_spec_a_102.py`` (A-100 / A-101 pattern).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
MIGRATIONS_DIR = REPO_ROOT / "migrations"
CORE_MIGRATION = REPO_ROOT / "src" / "backend" / "db" / "migrations" / "001_initial.sql"


def _migration_path() -> Path:
    """Return the V{NNN}__add_latest_reached_phase.sql (any NNN)."""
    matches = sorted(MIGRATIONS_DIR.glob("V*__add_latest_reached_phase.sql"))
    assert matches, (
        f"latest_reached_phase migration missing under {MIGRATIONS_DIR} "
        f"(expected V{{NNN}}__add_latest_reached_phase.sql)"
    )
    return matches[-1]


def _seed_v1_projects_only() -> sqlite3.Connection:
    """Create just the `projects` table from the v1 core DDL.

    The core schema file also defines phases/task_ledger/etc. with FKs we
    don't need here; we only want the pre-migration `projects` shape so
    the AC-1 backfill assertion has a stable fixture.
    """
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(
        """
        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            current_phase INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active'
                CHECK(status IN ('active','completed','archived','deleted')),
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        """
    )
    return conn


class TestAC1MigrationBackfills:
    """AC-1: 既有 project 的 latest_reached_phase = current_phase。"""

    def test_migration_backfills_latest_reached_phase_from_current_phase(self) -> None:
        conn = _seed_v1_projects_only()
        # Pre-migration rows at different current_phase values.
        rows = [
            ("proj_a", "A", "", 0),
            ("proj_b", "B", "", 3),
            ("proj_c", "C", "", 11),
        ]
        conn.executemany(
            "INSERT INTO projects (project_id, title, description, current_phase) "
            "VALUES (?, ?, ?, ?)",
            rows,
        )

        ddl = _migration_path().read_text(encoding="utf-8")
        conn.executescript(ddl)

        # Columns exist.
        cols = {r[1] for r in conn.execute("PRAGMA table_info(projects)").fetchall()}
        assert "latest_reached_phase" in cols, (
            f"latest_reached_phase column missing after migration (got {cols})"
        )
        assert "phase_history" in cols, (
            f"phase_history column missing after migration (got {cols})"
        )

        # Backfill: latest_reached_phase == current_phase for each row.
        backfilled = dict(
            conn.execute(
                "SELECT project_id, latest_reached_phase FROM projects"
            ).fetchall()
        )
        assert backfilled == {"proj_a": 0, "proj_b": 3, "proj_c": 11}, (
            f"backfill mismatch: {backfilled}"
        )

        # phase_history default is a valid empty JSON array string.
        histories = {
            r[0]: r[1]
            for r in conn.execute(
                "SELECT project_id, phase_history FROM projects"
            ).fetchall()
        }
        assert set(histories.values()) == {"[]"}, (
            f"phase_history default must be '[]', got {histories}"
        )


class TestAC3PhaseHistoryEntries:
    """AC-3: phase_history[] 每条含 reached_at/completed_at?/last_revision_at?。"""

    def test_phase_history_entries_carry_reached_completed_revision_timestamps(
        self,
    ) -> None:
        from src.shared.schemas.project_state import PhaseHistoryEntry, ProjectState

        # Required: phase + reached_at.
        entry = PhaseHistoryEntry(phase=3, reached_at="2026-04-20T10:00:00Z")
        assert entry.phase == 3
        assert entry.reached_at == "2026-04-20T10:00:00Z"
        assert entry.completed_at is None
        assert entry.last_revision_at is None

        # Optional fields accepted.
        full = PhaseHistoryEntry(
            phase=5,
            reached_at="2026-04-20T10:00:00Z",
            completed_at="2026-04-20T11:00:00Z",
            last_revision_at="2026-04-20T12:00:00Z",
        )
        assert full.completed_at == "2026-04-20T11:00:00Z"
        assert full.last_revision_at == "2026-04-20T12:00:00Z"

        # phase must stay within 0..11 (per spec).
        with pytest.raises(ValidationError):
            PhaseHistoryEntry(phase=12, reached_at="2026-04-20T10:00:00Z")

        # reached_at is mandatory.
        with pytest.raises(ValidationError):
            PhaseHistoryEntry(phase=3)  # type: ignore[call-arg]

        # Extra fields are forbidden (strict contract boundary).
        with pytest.raises(ValidationError):
            PhaseHistoryEntry(
                phase=3,
                reached_at="2026-04-20T10:00:00Z",
                note="nope",  # type: ignore[call-arg]
            )

        # ProjectState carries the new high-water mark + phase_history list.
        fields = ProjectState.model_fields
        assert "latest_reached_phase" in fields, (
            "ProjectState must expose latest_reached_phase (v3.16 extension)"
        )
        assert "phase_history" in fields, (
            "ProjectState must expose phase_history (v3.16 extension)"
        )
