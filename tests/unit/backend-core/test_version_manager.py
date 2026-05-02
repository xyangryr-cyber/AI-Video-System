"""Tests for [SPEC-C-005] Version Management & Review Supersede.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.5 + SPEC-3.2 AC-3.

Test strategy per AC (mapped from task card):

- AC-1 generate_artifact_increments_version: a `running` generate_artifact
  task whose `produces_version` matches the next-version slot is closed
  via VersionManager → `phases.artifact_version` ticks from N to N+1.

- AC-2 user_revision_increments_version: same path through VersionManager
  but for a `user_revision` task → also bumps version by 1. Proves the
  module treats both artifact-producing types identically (SPEC-3.5).

- AC-3 auto_create_review_for_new_version: after the bump, exactly one
  new `review` row exists in `task_ledger` with `target_version == new
  version`, status=`pending`, type=`review`.

- AC-4 old_reviews_superseded: a pre-existing `review` task targeting
  the OLD version is flipped to `superseded` (whether it was pending,
  queued, or running before). The superseded task ids appear in the
  returned list.

- AC-5 no_duplicate_pending_reviews: after the call, the SQL invariant
  "exactly one pending review row per (project_id, phase)" holds.

- AC-6 superseded_not_dispatched: pair the version bump with the
  Dispatcher and prove Dispatcher promotes the NEW review (target_version
  matches), not the superseded OLD review.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "src" / "backend"
SCHEMA_FILE = BACKEND_DIR / "db" / "schema.sql"


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _seed_project_and_phase(
    conn: sqlite3.Connection,
    project_id: str = "proj_c005",
    phase_num: int = 0,
    artifact_version: int = 0,
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


def _phase_version(conn: sqlite3.Connection, project_id: str, phase_num: int) -> int:
    row = conn.execute(
        "SELECT artifact_version FROM phases WHERE project_id = ? AND phase_num = ?",
        (project_id, phase_num),
    ).fetchone()
    assert row is not None
    return int(row[0])


def _start_artifact_task(
    engine, project_id: str, phase_num: int, task_type: str, produces_version: int
) -> str:
    """Create + queue + run a generate_artifact / user_revision task so
    VersionManager.complete_artifact_task can transition it to succeeded.
    """
    task_id = engine.create_task(
        project_id=project_id,
        phase=phase_num,
        task_type=task_type,
        produces_version=produces_version,
    )
    engine.update_task_status(task_id, "queued")
    engine.update_task_status(task_id, "running", agent_name="test_agent")
    return task_id


class TestAC1GenerateArtifactIncrementsVersion:
    """AC-1: `generate_artifact` completion increments
    `phases.artifact_version` by 1.
    """

    def test_generate_artifact_increments_version(self) -> None:
        from src.backend.engine.version_manager import VersionManager
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn, "proj_c005_a1", phase_num=2, artifact_version=3)

        engine = WorkflowEngine(conn)
        vm = VersionManager(engine)

        task_id = _start_artifact_task(
            engine, "proj_c005_a1", 2, "generate_artifact", 4
        )

        result = vm.complete_artifact_task(task_id)

        assert result.new_version == 4, (
            f"expected new_version=4 (3 -> 4), got {result.new_version}"
        )
        assert _phase_version(conn, "proj_c005_a1", 2) == 4, (
            "phases.artifact_version must persist the bumped value"
        )
        # Source task must end in 'succeeded' (single transition).
        task = engine.get_task(task_id)
        assert task is not None and task["status"] == "succeeded"


class TestAC2UserRevisionIncrementsVersion:
    """AC-2: `user_revision` completion increments
    `phases.artifact_version` by 1.
    """

    def test_user_revision_increments_version(self) -> None:
        from src.backend.engine.version_manager import VersionManager
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn, "proj_c005_a2", phase_num=1, artifact_version=7)

        engine = WorkflowEngine(conn)
        vm = VersionManager(engine)

        task_id = _start_artifact_task(engine, "proj_c005_a2", 1, "user_revision", 8)

        result = vm.complete_artifact_task(task_id)

        assert result.new_version == 8
        assert _phase_version(conn, "proj_c005_a2", 1) == 8


class TestAC3AutoCreateReviewForNewVersion:
    """AC-3: After version increment, a new `review` task is auto-created
    with `target_version` equal to the new version.
    """

    def test_auto_create_review_for_new_version(self) -> None:
        from src.backend.engine.version_manager import VersionManager
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn, "proj_c005_a3", phase_num=4, artifact_version=0)

        engine = WorkflowEngine(conn)
        vm = VersionManager(engine)

        artifact_task = _start_artifact_task(
            engine, "proj_c005_a3", 4, "generate_artifact", 1
        )
        result = vm.complete_artifact_task(artifact_task)

        assert result.new_review_task_id is not None
        new_review = engine.get_task(result.new_review_task_id)
        assert new_review is not None
        assert new_review["type"] == "review"
        assert new_review["status"] == "pending"
        assert new_review["target_version"] == 1
        assert new_review["produces_version"] is None
        assert new_review["phase"] == 4

        rows = conn.execute(
            "SELECT id, target_version FROM task_ledger "
            "WHERE project_id = ? AND phase = ? AND type = 'review' "
            "AND status = 'pending'",
            ("proj_c005_a3", 4),
        ).fetchall()
        assert len(rows) == 1, (
            f"expected exactly one pending review for new version, got {rows}"
        )
        assert rows[0][1] == result.new_version


class TestAC4OldReviewsSuperseded:
    """AC-4: Older pending/queued review tasks are set to `superseded`."""

    def test_old_reviews_superseded(self) -> None:
        from src.backend.engine.version_manager import VersionManager
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn, "proj_c005_a4", phase_num=0, artifact_version=2)

        engine = WorkflowEngine(conn)
        vm = VersionManager(engine)

        # Stale review pointing at version 2 (the OLD value).
        stale_pending = engine.create_task(
            project_id="proj_c005_a4",
            phase=0,
            task_type="review",
            target_version=2,
        )
        stale_queued = engine.create_task(
            project_id="proj_c005_a4",
            phase=0,
            task_type="review",
            target_version=2,
        )
        engine.update_task_status(stale_queued, "queued")

        artifact_task = _start_artifact_task(
            engine, "proj_c005_a4", 0, "generate_artifact", 3
        )
        result = vm.complete_artifact_task(artifact_task)

        assert result.new_version == 3

        # Both stale reviews must be 'superseded'.
        for tid in (stale_pending, stale_queued):
            row = engine.get_task(tid)
            assert row is not None
            assert row["status"] == "superseded", (
                f"stale review {tid} must be superseded; got {row['status']}"
            )

        assert set(result.superseded_review_task_ids) == {
            stale_pending,
            stale_queued,
        }


class TestAC5NoDuplicatePendingReviews:
    """AC-5: At most one pending review per (project_id, phase) after
    the version bump completes.
    """

    def test_no_duplicate_pending_reviews(self) -> None:
        from src.backend.engine.version_manager import VersionManager
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn, "proj_c005_a5", phase_num=2, artifact_version=1)

        engine = WorkflowEngine(conn)
        vm = VersionManager(engine)

        # A pending review for the OLD version exists when the new
        # artifact lands.
        engine.create_task(
            project_id="proj_c005_a5",
            phase=2,
            task_type="review",
            target_version=1,
        )

        artifact_task = _start_artifact_task(
            engine, "proj_c005_a5", 2, "generate_artifact", 2
        )
        vm.complete_artifact_task(artifact_task)

        rows = conn.execute(
            "SELECT id, target_version FROM task_ledger "
            "WHERE project_id = ? AND phase = ? AND type = 'review' "
            "AND status = 'pending'",
            ("proj_c005_a5", 2),
        ).fetchall()
        assert len(rows) == 1, (
            f"invariant broken: expected exactly 1 pending review, "
            f"got {len(rows)} → {rows}"
        )
        # The single survivor must point at the NEW version, not the old.
        assert rows[0][1] == 2

        # Distinct versions across pending rows for the same phase: must
        # never be more than one.
        distinct_versions = conn.execute(
            "SELECT COUNT(DISTINCT target_version) FROM task_ledger "
            "WHERE project_id = ? AND phase = ? AND type = 'review' "
            "AND status = 'pending'",
            ("proj_c005_a5", 2),
        ).fetchone()
        assert int(distinct_versions[0]) == 1


class TestAC6SupersededNotDispatched:
    """AC-6: Superseded review tasks are not picked up by Dispatcher."""

    def test_superseded_not_dispatched(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.version_manager import VersionManager
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn, "proj_c005_a6", phase_num=0, artifact_version=0)

        engine = WorkflowEngine(conn)
        vm = VersionManager(engine)
        dispatcher = Dispatcher(engine)

        stale_review = engine.create_task(
            project_id="proj_c005_a6",
            phase=0,
            task_type="review",
            target_version=0,
        )

        artifact_task = _start_artifact_task(
            engine, "proj_c005_a6", 0, "generate_artifact", 1
        )
        result = vm.complete_artifact_task(artifact_task)

        # Sanity: the new review row exists and is pending.
        new_review = engine.get_task(result.new_review_task_id)
        assert new_review is not None and new_review["status"] == "pending"
        assert engine.get_task(stale_review)["status"] == "superseded"

        # Run one dispatch tick -- the slot is free (artifact_task was
        # already moved to succeeded by VersionManager). The new review
        # must be promoted; the superseded review must NOT be touched.
        promoted = dispatcher.dispatch_once()
        assert promoted == [result.new_review_task_id], (
            f"Dispatcher must queue ONLY the new pending review; got {promoted}"
        )
        assert engine.get_task(stale_review)["status"] == "superseded", (
            "superseded task must not be touched by the dispatcher"
        )


class TestVersionManagerInputValidation:
    """Defensive checks: VersionManager rejects ineligible inputs so
    callers can't accidentally bump the version off a `review` task or
    a non-existent task id.
    """

    def test_rejects_review_task_type(self) -> None:
        from src.backend.engine.version_manager import VersionManager
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn, "proj_c005_v", phase_num=0, artifact_version=1)

        engine = WorkflowEngine(conn)
        vm = VersionManager(engine)

        review = engine.create_task(
            project_id="proj_c005_v",
            phase=0,
            task_type="review",
            target_version=1,
        )
        engine.update_task_status(review, "queued")
        engine.update_task_status(review, "running", agent_name="test_agent")

        with pytest.raises(ValueError):
            vm.complete_artifact_task(review)

    def test_rejects_unknown_task(self) -> None:
        from src.backend.engine.version_manager import VersionManager
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn, "proj_c005_x", phase_num=0, artifact_version=0)

        engine = WorkflowEngine(conn)
        vm = VersionManager(engine)

        with pytest.raises(ValueError):
            vm.complete_artifact_task("t_999999")
