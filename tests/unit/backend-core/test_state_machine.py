"""Tests for [SPEC-C-002] Task State Machine (AC-4..AC-8).

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.6 transition matrix.

AC coverage:
  - AC-4 succeeded -> running raises IllegalStateTransition
  - AC-5 failed -> queued raises IllegalStateTransition
  - AC-6 all 10 legal transitions pass
  - AC-7 every legal transition writes an event
  - AC-8 stale review (target_version != phase.artifact_version) -> superseded
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

LEGAL_TRANSITIONS = [
    ("pending", "queued"),
    ("pending", "superseded"),
    ("pending", "failed"),
    ("queued", "running"),
    ("queued", "superseded"),
    ("queued", "failed"),
    ("running", "succeeded"),
    ("running", "failed"),
    ("running", "superseded"),
    ("running", "timeout"),
]

# ``from -> event_type`` expected on each transition (by destination).
EVENT_BY_TARGET = {
    "queued": "task.queued",
    "running": "task.started",
    "succeeded": "task.completed",
    "failed": "task.failed",
    "superseded": "task.superseded",
    "timeout": "task.failed",
}


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _seed_project_and_phase(
    conn: sqlite3.Connection,
    project_id: str = "proj_c002_sm",
    phase_num: int = 3,
    artifact_version: int = 2,
) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name, "
        "artifact_version) VALUES(?, ?, ?, ?)",
        (project_id, phase_num, f"P{phase_num}", artifact_version),
    )
    conn.commit()


class TestAC4SucceededToRunningRaises:
    """AC-4: succeeded -> running raises IllegalStateTransition."""

    def test_succeeded_to_running_raises(self):
        from src.backend.engine.state_machine import (
            IllegalStateTransition,
            ensure_legal_transition,
        )

        with pytest.raises(IllegalStateTransition):
            ensure_legal_transition("succeeded", "running")


class TestAC5FailedToQueuedRaises:
    """AC-5: failed -> queued raises IllegalStateTransition."""

    def test_failed_to_queued_raises(self):
        from src.backend.engine.state_machine import (
            IllegalStateTransition,
            ensure_legal_transition,
        )

        with pytest.raises(IllegalStateTransition):
            ensure_legal_transition("failed", "queued")


class TestAC6AllLegalTransitions:
    """AC-6: all 10 legal transitions from the SPEC-3.6 matrix pass."""

    def test_all_legal_transitions(self):
        from src.backend.engine.state_machine import ensure_legal_transition

        for src, dst in LEGAL_TRANSITIONS:
            # Must not raise; any raise means the matrix is incomplete.
            ensure_legal_transition(src, dst)

    def test_transition_count_is_ten(self):
        from src.backend.engine.state_machine import LEGAL_TRANSITIONS as LT

        assert len(LT) == 10, (
            f"SPEC-3.6 matrix has exactly 10 legal transitions; got {len(LT)}"
        )

    def test_terminal_states_have_no_outbound_transitions(self):
        from src.backend.engine.state_machine import (
            IllegalStateTransition,
            ensure_legal_transition,
        )

        terminals = ("succeeded", "failed", "superseded", "timeout")
        for terminal in terminals:
            for target in ("pending", "queued", "running"):
                with pytest.raises(IllegalStateTransition):
                    ensure_legal_transition(terminal, target)


class TestAC7TransitionWritesEvent:
    """AC-7: every legal transition writes an event row with matching type."""

    def test_queued_transition_writes_task_queued(self):
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)
        engine = WorkflowEngine(conn)
        task_id = engine.create_task(
            project_id="proj_c002_sm",
            phase=3,
            task_type="generate_artifact",
            params={
                "phase_name": "P3",
                "input_refs": ["phase_2/script.md"],
            },
        )

        engine.update_task_status(task_id, "queued")
        types = [
            row[0]
            for row in conn.execute(
                "SELECT type FROM events WHERE project_id=? ORDER BY id",
                ("proj_c002_sm",),
            ).fetchall()
        ]
        assert "task.queued" in types, (
            f"queued transition must emit task.queued; got {types}"
        )

    def test_running_transition_writes_task_started(self):
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)
        engine = WorkflowEngine(conn)
        task_id = engine.create_task(
            project_id="proj_c002_sm",
            phase=3,
            task_type="generate_artifact",
            params={
                "phase_name": "P3",
                "input_refs": ["phase_2/script.md"],
            },
        )
        engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="ScriptAgent")

        types = [
            row[0]
            for row in conn.execute(
                "SELECT type FROM events WHERE project_id=? ORDER BY id",
                ("proj_c002_sm",),
            ).fetchall()
        ]
        assert "task.started" in types, (
            f"running transition must emit task.started; got {types}"
        )

    def test_succeeded_transition_writes_task_completed(self):
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)
        engine = WorkflowEngine(conn)
        task_id = engine.create_task(
            project_id="proj_c002_sm",
            phase=3,
            task_type="generate_artifact",
            params={
                "phase_name": "P3",
                "input_refs": ["phase_2/script.md"],
            },
        )
        engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="ScriptAgent")
        engine.update_task_status(
            task_id, "succeeded", result_ref="phase_3/script_v1.md"
        )

        types = [
            row[0]
            for row in conn.execute(
                "SELECT type FROM events WHERE project_id=? ORDER BY id",
                ("proj_c002_sm",),
            ).fetchall()
        ]
        assert "task.completed" in types, (
            f"succeeded transition must emit task.completed; got {types}"
        )

    def test_failed_transition_writes_task_failed(self):
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)
        engine = WorkflowEngine(conn)
        task_id = engine.create_task(
            project_id="proj_c002_sm",
            phase=3,
            task_type="generate_artifact",
            params={
                "phase_name": "P3",
                "input_refs": ["phase_2/script.md"],
            },
        )
        engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="ScriptAgent")
        engine.update_task_status(
            task_id,
            "failed",
            error_code="EVID_3001",
            error_message="boom",
        )

        types = [
            row[0]
            for row in conn.execute(
                "SELECT type FROM events WHERE project_id=? ORDER BY id",
                ("proj_c002_sm",),
            ).fetchall()
        ]
        assert "task.failed" in types, (
            f"failed transition must emit task.failed; got {types}"
        )

    def test_illegal_transition_via_engine_raises(self):
        """Calling update_task_status with an illegal transition raises."""
        from src.backend.engine.state_machine import IllegalStateTransition
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)
        engine = WorkflowEngine(conn)
        task_id = engine.create_task(
            project_id="proj_c002_sm",
            phase=3,
            task_type="generate_artifact",
            params={
                "phase_name": "P3",
                "input_refs": ["phase_2/script.md"],
            },
        )
        # drive to succeeded
        engine.update_task_status(task_id, "queued")
        engine.update_task_status(task_id, "running", agent_name="ScriptAgent")
        engine.update_task_status(task_id, "succeeded")
        with pytest.raises(IllegalStateTransition):
            engine.update_task_status(task_id, "running")


class TestAC8StaleReviewSuperseded:
    """AC-8: review.target_version != phase.artifact_version -> superseded."""

    def test_stale_review_is_superseded(self):
        """Two pending review tasks for the same phase: one matches the
        current artifact_version (stays pending), one is stale (becomes
        superseded after supersede_stale_reviews runs).
        """
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(
            conn, project_id="proj_c002_sm", phase_num=3, artifact_version=2
        )
        engine = WorkflowEngine(conn)

        stale_id = engine.create_task(
            project_id="proj_c002_sm",
            phase=3,
            task_type="review",
            params={
                "phase_name": "P3",
                "reviewer_name": "StyleReviewer",
                "artifact_path": "phase_3/script_v1.md",
            },
            target_version=1,  # < phase.artifact_version=2 -> stale
        )
        fresh_id = engine.create_task(
            project_id="proj_c002_sm",
            phase=3,
            task_type="review",
            params={
                "phase_name": "P3",
                "reviewer_name": "StyleReviewer",
                "artifact_path": "phase_3/script_v2.md",
            },
            target_version=2,  # == phase.artifact_version -> fresh
        )

        engine.supersede_stale_reviews(project_id="proj_c002_sm", phase_num=3)

        stale_row = conn.execute(
            "SELECT status FROM task_ledger WHERE id=?", (stale_id,)
        ).fetchone()
        fresh_row = conn.execute(
            "SELECT status FROM task_ledger WHERE id=?", (fresh_id,)
        ).fetchone()

        assert stale_row is not None and fresh_row is not None
        assert stale_row[0] == "superseded", (
            f"stale review (target_version=1) must be superseded; "
            f"got status={stale_row[0]}"
        )
        assert fresh_row[0] != "superseded", (
            f"fresh review (target_version=2) must not be superseded; "
            f"got status={fresh_row[0]}"
        )
        # The supersede event must land.
        types = [
            row[0]
            for row in conn.execute(
                "SELECT type FROM events WHERE project_id=? ORDER BY id",
                ("proj_c002_sm",),
            ).fetchall()
        ]
        assert "task.superseded" in types, (
            f"superseding must emit task.superseded; got {types}"
        )
