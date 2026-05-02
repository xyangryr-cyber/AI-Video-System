"""[SPEC-G-000d] Phase 8 task routing tests -- KeyframeRenderAgent.

AC-8.1: success path → task_ledger.status = succeeded
AC-8.2: failure path → task_ledger.status = failed, error_code = AGENT_FAILURE
AC-8.3: params forwarded to agent methods
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
        "VALUES('proj_test', 8, 'P8')"
    )
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type, status, params) "
        "VALUES('task_p8', 'proj_test', 8, 'generate_artifact', 'pending', '{}')"
    )
    conn.commit()
    from src.backend.engine.workflow_engine import WorkflowEngine

    return WorkflowEngine(conn=conn)


def _mock_keyframe_agent():
    agent = MagicMock()
    agent.render_keyframes.return_value = [
        {
            "shot_id": "shot_001",
            "render_path": "phase_8/shot_001.png",
            "degraded": False,
        },
    ]
    agent.handle_failed_shot.return_value = {
        "shot_id": "shot_001",
        "degraded": True,
        "fallback_type": "text_card",
        "reason": "test",
        "render_path": "phase_8/shot_001_fallback.png",
    }
    return agent


class TestPhase8SuccessPath:
    def test_phase8_success_path_sets_succeeded(self, engine):
        agent = _mock_keyframe_agent()

        with patch("src.backend.workers.tasks.KeyframeRenderAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase8_keyframe

                run_phase8_keyframe.call_local(
                    "task_p8",
                    {"storyboard": [{"shot_id": "shot_001", "type": "template"}]},
                )

        task = engine.get_task("task_p8")
        assert task is not None
        assert task["status"] == "succeeded"


class TestPhase8FailurePath:
    def test_phase8_failure_path_sets_failed(self, engine):
        agent = MagicMock()
        agent.render_keyframes.side_effect = RuntimeError("Keyframe render failed")

        with patch("src.backend.workers.tasks.KeyframeRenderAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase8_keyframe

                with pytest.raises(RuntimeError, match="Keyframe render failed"):
                    run_phase8_keyframe.call_local("task_p8", {"storyboard": []})

        task = engine.get_task("task_p8")
        assert task is not None
        assert task["status"] == "failed"


class TestPhase8ParamsForwarded:
    def test_phase8_params_forwarded_to_agent(self, engine):
        agent = MagicMock()
        agent.render_keyframes.return_value = [
            {"shot_id": "shot_001", "render_path": "phase_8/shot_001.png"},
        ]
        agent.handle_failed_shot.return_value = {}

        storyboard = [
            {"shot_id": "shot_001", "type": "template", "template_type": "text_card"}
        ]

        with patch("src.backend.workers.tasks.KeyframeRenderAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase8_keyframe

                run_phase8_keyframe.call_local("task_p8", {"storyboard": storyboard})

        agent.render_keyframes.assert_called_once_with(storyboard=storyboard)
