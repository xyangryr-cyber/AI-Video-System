"""Tests for [SPEC-C-004] Phase Rollback (AC-1, AC-4).

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.4.

Test strategy:

- AC-1 rollback_invalidates_downstream: seed a project with current_phase=5
  and rows in ``phases`` for P0..P5, then call
  ``PhaseOps.rollback(project_id, target_phase=2)``. Phase rows for
  phase_num 3, 4, 5 must flip to ``status='invalidated'``; phase 0/1/2
  must be untouched; ``projects.current_phase`` must drop to 2.

- AC-4 rollback_impact_analysis: ``PhaseOps.analyze_rollback`` returns
  a report BEFORE mutating state. The report names the affected phase
  numbers and the per-phase ``artifact_version`` / segment counts so
  the UI can show the user what rollback will drop. Running
  ``analyze_rollback`` MUST NOT mutate ``phases`` / ``projects``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "src" / "backend"
SCHEMA_FILE = BACKEND_DIR / "db" / "schema.sql"


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _seed_project_with_phases(
    conn: sqlite3.Connection,
    project_id: str,
    current_phase: int,
    artifact_versions: dict[int, int] | None = None,
) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description, current_phase) "
        "VALUES(?, ?, ?, ?)",
        (project_id, "t", "d", current_phase),
    )
    versions = artifact_versions or {}
    for p in range(current_phase + 1):
        av = int(versions.get(p, 0))
        status = "completed" if p < current_phase else "active"
        conn.execute(
            "INSERT INTO phases(project_id, phase_num, phase_name, "
            "status, artifact_version, artifact_path) "
            "VALUES(?, ?, ?, ?, ?, ?)",
            (
                project_id,
                p,
                f"P{p}",
                status,
                av,
                f"phase_{p}/artifact_v{av}.json" if av else None,
            ),
        )
    conn.commit()


def _phase_status(conn: sqlite3.Connection, project_id: str, phase_num: int) -> str:
    row = conn.execute(
        "SELECT status FROM phases WHERE project_id = ? AND phase_num = ?",
        (project_id, phase_num),
    ).fetchone()
    assert row is not None, f"phase {phase_num} missing"
    return str(row[0])


def _current_phase(conn: sqlite3.Connection, project_id: str) -> int:
    row = conn.execute(
        "SELECT current_phase FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    assert row is not None
    return int(row[0])


class TestAC1RollbackInvalidatesDownstream:
    """AC-1: Rollback to Phase X marks Phase X+1..current_phase invalidated."""

    def test_rollback_invalidates_downstream(self) -> None:
        from src.backend.engine.phase_ops import PhaseOps
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_with_phases(
            conn,
            "proj_c004_r",
            current_phase=5,
            artifact_versions={0: 1, 1: 1, 2: 2, 3: 1, 4: 1, 5: 1},
        )

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        result = ops.rollback("proj_c004_r", target_phase=2)

        # Current phase dropped to target.
        assert _current_phase(conn, "proj_c004_r") == 2
        # Phases 3/4/5 invalidated.
        for p in (3, 4, 5):
            assert _phase_status(conn, "proj_c004_r", p) == "invalidated", (
                f"phase {p} must be invalidated after rollback to 2"
            )
        # Phases 0/1/2 untouched.
        for p in (0, 1):
            assert _phase_status(conn, "proj_c004_r", p) == "completed", (
                f"phase {p} (< target) must not be invalidated"
            )
        assert _phase_status(conn, "proj_c004_r", 2) in (
            "active",
            "completed",
        ), "target phase must not be invalidated"

        # Result reports the invalidated set.
        assert result.target_phase == 2
        assert sorted(result.invalidated_phases) == [3, 4, 5]

    def test_rollback_emits_phase_invalidated_event_per_phase(self) -> None:
        from src.backend.engine.phase_ops import PhaseOps
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_with_phases(conn, "proj_c004_r2", current_phase=4)

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        ops.rollback("proj_c004_r2", target_phase=1)

        events = conn.execute(
            "SELECT type, payload FROM events "
            "WHERE project_id = ? AND type = ? ORDER BY id ASC",
            ("proj_c004_r2", "phase.invalidated"),
        ).fetchall()
        # One event per invalidated phase (2, 3, 4).
        assert len(events) == 3, (
            f"expected 3 phase.invalidated events, got {len(events)}"
        )

    def test_rollback_invalid_target_raises(self) -> None:
        from src.backend.engine.phase_ops import (
            InvalidRollbackTarget,
            PhaseOps,
        )
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_with_phases(conn, "proj_c004_r3", current_phase=3)

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        # Target >= current is not a rollback.
        try:
            ops.rollback("proj_c004_r3", target_phase=3)
        except InvalidRollbackTarget as exc:
            assert exc.error_code == "EVID_2004"
        else:
            raise AssertionError(
                "rollback(target=current) must raise InvalidRollbackTarget"
            )


class TestAC4RollbackImpactAnalysis:
    """AC-4: analyze_rollback returns impact report without mutation."""

    def test_analyze_rollback_reports_affected_phases_and_versions(self) -> None:
        from src.backend.engine.phase_ops import PhaseOps
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_with_phases(
            conn,
            "proj_c004_ia",
            current_phase=5,
            artifact_versions={0: 1, 1: 1, 2: 2, 3: 3, 4: 2, 5: 1},
        )

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        impact = ops.analyze_rollback("proj_c004_ia", target_phase=2)

        assert impact.target_phase == 2
        assert impact.current_phase == 5
        assert sorted(impact.invalidated_phases) == [3, 4, 5]
        # Per-phase artifact_version snapshot so UI can show "3 artifacts dropped".
        assert impact.affected_artifact_versions == {3: 3, 4: 2, 5: 1}
        # Segment count = sum of versions (proxy for affected segments in V1).
        assert impact.affected_segment_count == 3 + 2 + 1

    def test_analyze_rollback_is_read_only(self) -> None:
        from src.backend.engine.phase_ops import PhaseOps
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_with_phases(conn, "proj_c004_ro", current_phase=4)

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        ops.analyze_rollback("proj_c004_ro", target_phase=1)

        # No mutation: current_phase still 4, phases still completed/active.
        assert _current_phase(conn, "proj_c004_ro") == 4
        for p in (2, 3, 4):
            assert _phase_status(conn, "proj_c004_ro", p) != "invalidated", (
                f"analyze_rollback must not mutate phase {p}"
            )
