"""[SPEC-G-000d] Phase 4 task routing tests -- TTSAgent.

AC-4.1: success path → task_ledger.status = succeeded
AC-4.2: failure path → task_ledger.status = failed, error_code = AGENT_FAILURE
AC-4.3: params forwarded to agent methods
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
        "VALUES('proj_test', 4, 'P4')"
    )
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type, status, params) "
        "VALUES('task_p4', 'proj_test', 4, 'generate_artifact', 'pending', '{}')"
    )
    conn.commit()
    from src.backend.engine.workflow_engine import WorkflowEngine

    return WorkflowEngine(conn=conn)


def _mock_tts_agent():
    agent = MagicMock()
    agent.select_voice_candidates.return_value = [{"voice_id": "voice_zh_female_01"}]
    agent.build_timeline.return_value = {"segments": [], "total_duration_sec": 0}
    return agent


class TestPhase4SuccessPath:
    def test_phase4_success_path_sets_succeeded(self, engine):
        agent = _mock_tts_agent()

        with patch("src.backend.workers.tasks.TTSAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase4_tts

                run_phase4_tts.call_local(
                    "task_p4",
                    {
                        "polished_script": {
                            "segments": [{"segment_id": "s1", "content": "hello"}]
                        }
                    },
                )

        task = engine.get_task("task_p4")
        assert task is not None
        assert task["status"] == "succeeded"


class TestPhase4FailurePath:
    def test_phase4_failure_path_sets_failed(self, engine):
        agent = MagicMock()
        agent.select_voice_candidates.side_effect = RuntimeError("TTS synthesis failed")

        with patch("src.backend.workers.tasks.TTSAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase4_tts

                with pytest.raises(RuntimeError, match="TTS synthesis failed"):
                    run_phase4_tts.call_local(
                        "task_p4", {"polished_script": {"segments": []}}
                    )

        task = engine.get_task("task_p4")
        assert task is not None
        assert task["status"] == "failed"


class TestPhase4ParamsForwarded:
    def test_phase4_params_forwarded_to_agent(self, engine):
        agent = _mock_tts_agent()

        polished_script = {"segments": [{"segment_id": "s1", "content": "test"}]}
        voice_prefs = {"preferred_voice_id": "voice_zh_male_01"}

        with patch("src.backend.workers.tasks.TTSAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase4_tts

                run_phase4_tts.call_local(
                    "task_p4",
                    {
                        "polished_script": polished_script,
                        "voice_preferences": voice_prefs,
                    },
                )

        agent.select_voice_candidates.assert_called_once_with(
            polished_script=polished_script,
            voice_preferences=voice_prefs,
        )
        agent.build_timeline.assert_called_once_with(
            polished_script=polished_script,
            voice_id="voice_zh_female_01",
        )
