"""[SPEC-G-000d] Phase 10 task routing tests -- RoughCutAgent.

AC-10.1: success path → task_ledger.status = succeeded
AC-10.2: failure path → task_ledger.status = failed, error_code = AGENT_FAILURE
AC-10.3: params forwarded to agent methods
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

SCHEMA_FILE = (
    Path(__file__).resolve().parents[3] / "src" / "backend" / "db" / "schema.sql"
)


@pytest.fixture
def engine():
    conn = sqlite3.connect(":memory:")
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.execute(
        "INSERT INTO projects(project_id, title, description) "
        "VALUES('proj_test', 't', 'd')"
    )
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name) "
        "VALUES('proj_test', 10, 'P10')"
    )
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type, status, params) "
        "VALUES('task_p10', 'proj_test', 10, 'generate_artifact', 'pending', '{}')"
    )
    conn.commit()
    from src.backend.engine.workflow_engine import WorkflowEngine

    return WorkflowEngine(conn=conn)


class TestPhase10SuccessPath:
    def test_phase10_success_path_sets_succeeded(self, engine):
        agent = MagicMock()
        agent.compose.return_value = {
            "rough_cut_path": "phase_10/rough_cut.mp4",
            "duration_seconds": 30.0,
            "resolution": "1920x1080",
            "fps": 30,
        }

        with patch("src.backend.workers.tasks.RoughCutAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase10_rough_cut

                run_phase10_rough_cut.call_local(
                    "task_p10",
                    {
                        "storyboard": [],
                        "timeline": {"total_duration_sec": 30.0},
                        "keyframe_renders": [],
                    },
                )

        task = engine.get_task("task_p10")
        assert task is not None
        assert task["status"] == "succeeded"


class TestPhase10FailurePath:
    def test_phase10_failure_path_sets_failed(self, engine):
        agent = MagicMock()
        agent.compose.side_effect = RuntimeError("Rough cut composition failed")

        with patch("src.backend.workers.tasks.RoughCutAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase10_rough_cut

                with pytest.raises(RuntimeError, match="Rough cut composition failed"):
                    run_phase10_rough_cut.call_local(
                        "task_p10",
                        {"storyboard": [], "timeline": {}, "keyframe_renders": []},
                    )

        task = engine.get_task("task_p10")
        assert task is not None
        assert task["status"] == "failed"


class TestPhase10ParamsForwarded:
    def test_phase10_params_forwarded_to_agent(self, engine):
        agent = MagicMock()
        agent.compose.return_value = {
            "rough_cut_path": "phase_10/rough_cut.mp4",
        }

        storyboard = [
            {"shot_id": "s1", "time_range": {"start_seconds": 0, "end_seconds": 5}}
        ]
        timeline = {"total_duration_sec": 30.0, "segments": []}
        keyframe_renders = [{"shot_id": "s1", "render_path": "phase_8/s1.png"}]

        with patch("src.backend.workers.tasks.RoughCutAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase10_rough_cut

                run_phase10_rough_cut.call_local(
                    "task_p10",
                    {
                        "storyboard": storyboard,
                        "timeline": timeline,
                        "keyframe_renders": keyframe_renders,
                    },
                )

        agent.compose.assert_called_once_with(
            storyboard=storyboard,
            timeline=timeline,
            keyframe_renders=keyframe_renders,
        )
