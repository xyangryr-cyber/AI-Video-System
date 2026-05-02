"""[SPEC-G-000d] Phase 5 task routing tests -- BGMAgent.

AC-5.1: success path → task_ledger.status = succeeded
AC-5.2: failure path → task_ledger.status = failed, error_code = AGENT_FAILURE
AC-5.3: params forwarded to agent methods
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
        "VALUES('proj_test', 5, 'P5')"
    )
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type, status, params) "
        "VALUES('task_p5', 'proj_test', 5, 'generate_artifact', 'pending', '{}')"
    )
    conn.commit()
    from src.backend.engine.workflow_engine import WorkflowEngine

    return WorkflowEngine(conn=conn)


class TestPhase5SuccessPath:
    def test_phase5_success_path_sets_succeeded(self, engine):
        agent = MagicMock()
        agent.produce_emotion_curve.return_value = {
            "segments": [],
            "transition_points": [],
        }
        agent.select_bgm_candidates.return_value = [
            {
                "track_id": "local_upbeat_01",
                "energy_score": 8,
                "source": "local_library",
            },
        ]

        with patch("src.backend.workers.tasks.BGMAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase5_bgm_preview

                run_phase5_bgm_preview.call_local(
                    "task_p5",
                    {"timeline": {"segments": [], "total_duration_sec": 0}},
                )

        task = engine.get_task("task_p5")
        assert task is not None
        assert task["status"] == "succeeded"


class TestPhase5FailurePath:
    def test_phase5_failure_path_sets_failed(self, engine):
        agent = MagicMock()
        agent.produce_emotion_curve.side_effect = RuntimeError("BGM analysis failed")

        with patch("src.backend.workers.tasks.BGMAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase5_bgm_preview

                with pytest.raises(RuntimeError, match="BGM analysis failed"):
                    run_phase5_bgm_preview.call_local(
                        "task_p5", {"timeline": {"segments": []}}
                    )

        task = engine.get_task("task_p5")
        assert task is not None
        assert task["status"] == "failed"


class TestPhase5ParamsForwarded:
    def test_phase5_params_forwarded_to_agent(self, engine):
        agent = MagicMock()
        agent.produce_emotion_curve.return_value = {
            "segments": [{"segment_id": "s1", "emotion": "neutral", "energy": 5}],
            "transition_points": [0.0],
        }
        agent.select_bgm_candidates.return_value = []

        timeline = {
            "segments": [{"segment_id": "s1", "emotion_tone": "calm", "start_sec": 0.0}]
        }

        with patch("src.backend.workers.tasks.BGMAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase5_bgm_preview

                run_phase5_bgm_preview.call_local("task_p5", {"timeline": timeline})

        agent.produce_emotion_curve.assert_called_once_with(
            timeline=timeline,
        )
        agent.select_bgm_candidates.assert_called_once()
