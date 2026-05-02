"""Tests for [SPEC-C-002] Task Data Structures (AC-1..AC-3).

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.2 and
docs/specs/SPEC-A-contracts.md SPEC-1B (task_ledger DDL).

AC coverage:
  - AC-1 task_id_format_monotonic
  - AC-2 review_no_produces_version / generate_artifact_no_target_version
  - AC-3 eight_task_types_no_await_user
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

TASK_ID_RE = re.compile(r"^t_\d{6}$")


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _seed_project_and_phase(
    conn: sqlite3.Connection,
    project_id: str = "proj_c002",
    phase_num: int = 0,
) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name) VALUES(?, ?, ?)",
        (project_id, phase_num, f"P{phase_num}"),
    )
    conn.commit()


class TestAC1TaskIdFormat:
    """AC-1: Task id follows ``t_<6-digit>`` monotonically increasing format."""

    def test_task_id_format_monotonic(self):
        """Three consecutive create_task calls yield strictly increasing
        ``t_<6-digit>`` IDs starting at ``t_000001`` for a fresh project.
        """
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)
        engine = WorkflowEngine(conn)

        ids = [
            engine.create_task(
                project_id="proj_c002",
                phase=0,
                task_type="generate_artifact",
            )
            for _ in range(3)
        ]
        assert all(TASK_ID_RE.match(tid) for tid in ids), (
            f"each id must match t_<6-digit>; got {ids}"
        )
        # Monotonic: sort order equals creation order.
        assert ids == sorted(ids), (
            f"task ids must be monotonically increasing; got {ids}"
        )
        # Distinct.
        assert len(set(ids)) == 3, f"task ids must be distinct; got {ids}"

    def test_task_id_seeds_from_existing_max(self):
        """A new engine on an already-populated DB must not recycle IDs.

        Guards against the degenerate counter-from-1 impl by inserting a
        high-valued row first and asserting the next id strictly exceeds it.
        """
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)
        engine = WorkflowEngine(conn)
        # Use engine to establish that t_000042 is reserved.
        engine.create_task(
            project_id="proj_c002",
            phase=0,
            task_type="generate_artifact",
            task_id="t_000042",
        )
        engine2 = WorkflowEngine(conn)
        next_id = engine2.create_task(
            project_id="proj_c002",
            phase=0,
            task_type="generate_artifact",
        )
        assert next_id > "t_000042", (
            f"new engine must seed next id from DB MAX; got {next_id} after t_000042"
        )


class TestAC2FieldConstraintsByTaskType:
    """AC-2: ``review`` task has no ``produces_version``; ``generate_artifact``
    has no ``target_version``."""

    def test_review_no_produces_version(self):
        """Constructing a review Task with ``produces_version`` must fail."""
        from src.backend.engine.task_types import Task, TaskType

        with pytest.raises((ValueError, TypeError)):
            Task(
                id="t_000001",
                project_id="proj_c002",
                phase=3,
                type=TaskType.REVIEW,
                produces_version=1,  # forbidden for review
                target_version=1,
                params={
                    "phase_name": "P3",
                    "reviewer_name": "StyleReviewer",
                    "artifact_path": "phase_3/script_v1.md",
                },
            )

    def test_generate_artifact_no_target_version(self):
        """generate_artifact Task with ``target_version`` must fail."""
        from src.backend.engine.task_types import Task, TaskType

        with pytest.raises((ValueError, TypeError)):
            Task(
                id="t_000002",
                project_id="proj_c002",
                phase=2,
                type=TaskType.GENERATE_ARTIFACT,
                produces_version=1,
                target_version=1,  # forbidden for generate_artifact
                params={
                    "phase_name": "P2",
                    "input_refs": ["phase_1/outline_v1.json"],
                },
            )

    def test_review_requires_target_version(self):
        """Review Task must carry ``target_version`` (SPEC-3.5 supersede)."""
        from src.backend.engine.task_types import Task, TaskType

        with pytest.raises((ValueError, TypeError)):
            Task(
                id="t_000003",
                project_id="proj_c002",
                phase=3,
                type=TaskType.REVIEW,
                target_version=None,  # required for review
                params={
                    "phase_name": "P3",
                    "reviewer_name": "StyleReviewer",
                    "artifact_path": "phase_3/script_v1.md",
                },
            )

    def test_generate_artifact_happy_path(self):
        """Well-formed generate_artifact Task validates clean."""
        from src.backend.engine.task_types import Task, TaskType

        task = Task(
            id="t_000004",
            project_id="proj_c002",
            phase=2,
            type=TaskType.GENERATE_ARTIFACT,
            produces_version=1,
            params={
                "phase_name": "P2",
                "input_refs": ["phase_1/outline_v1.json"],
            },
        )
        assert task.type == TaskType.GENERATE_ARTIFACT
        assert task.produces_version == 1
        assert task.target_version is None


class TestAC3EightTaskTypes:
    """AC-3: 8 task types enumerated; no ``await_user`` type exists."""

    def test_eight_task_types_no_await_user(self):
        """The TaskType enum carries exactly the 14 canonical values
        (8 original + 6 phase-level types from SPEC-G-000-pre)."""
        from src.backend.engine.task_types import TaskType

        expected = {
            "generate_artifact",
            "regenerate_section",
            "user_revision",
            "review",
            "research",
            "verify",
            "cross_check",
            "user_annotation",
            "generate_narration",
            "preview_mix",
            "plan_layout",
            "render_keyframes",
            "compose_rough_cut",
            "export_final",
        }
        values = {t.value for t in TaskType}
        assert values == expected, (
            f"TaskType must contain all 14 canonical values; "
            f"got {values}, diff={values ^ expected}"
        )
        assert "await_user" not in values, (
            "await_user MUST NOT appear in TaskType (SPEC-3.2)"
        )


class TestG000PrePhaseTaskTypes:
    """SPEC-G-000-pre: 6 phase-level TaskType values added.

    Each new type behaves like generate_artifact:
    allows produces_version, forbids target_version.
    """

    PHASE_TYPES = [
        "generate_narration",
        "preview_mix",
        "plan_layout",
        "render_keyframes",
        "compose_rough_cut",
        "export_final",
    ]

    def test_generate_narration_type_exists(self):
        from src.backend.engine.task_types import TaskType

        assert TaskType.GENERATE_NARRATION.value == "generate_narration"

    def test_preview_mix_type_exists(self):
        from src.backend.engine.task_types import TaskType

        assert TaskType.PREVIEW_MIX.value == "preview_mix"

    def test_all_6_phase_types_in_enum(self):
        from src.backend.engine.task_types import TaskType

        values = {t.value for t in TaskType}
        for pt in self.PHASE_TYPES:
            assert pt in values, f"{pt} must be in TaskType enum"

    def test_generate_narration_allows_produces_version(self):
        from src.backend.engine.task_types import Task, TaskType

        task = Task(
            id="t_000010",
            project_id="proj_g000",
            phase=4,
            type=TaskType.GENERATE_NARRATION,
            produces_version=1,
        )
        assert task.produces_version == 1
        assert task.target_version is None

    def test_preview_mix_allows_produces_version(self):
        from src.backend.engine.task_types import Task, TaskType

        task = Task(
            id="t_000011",
            project_id="proj_g000",
            phase=5,
            type=TaskType.PREVIEW_MIX,
            produces_version=2,
        )
        assert task.produces_version == 2
        assert task.target_version is None

    def test_preview_mix_rejects_target_version(self):
        from src.backend.engine.task_types import Task, TaskType

        with pytest.raises((ValueError, TypeError)):
            Task(
                id="t_000012",
                project_id="proj_g000",
                phase=5,
                type=TaskType.PREVIEW_MIX,
                produces_version=1,
                target_version=1,
            )

    def test_all_6_phase_types_reject_target_version(self):
        from src.backend.engine.task_types import Task, TaskType

        for pt_value in self.PHASE_TYPES:
            pt = TaskType(pt_value)
            with pytest.raises((ValueError, TypeError)):
                Task(
                    id="t_000020",
                    project_id="proj_g000",
                    phase=1,
                    type=pt,
                    produces_version=1,
                    target_version=1,
                )
