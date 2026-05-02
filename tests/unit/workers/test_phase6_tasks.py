"""[SPEC-G-000d] Phase 6 task routing tests -- SFXAgent.

AC-6.1: success path → task_ledger.status = succeeded
AC-6.2: failure path → task_ledger.status = failed, error_code = AGENT_FAILURE
AC-6.3: params forwarded to agent methods
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
        "VALUES('proj_test', 6, 'P6')"
    )
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type, status, params) "
        "VALUES('task_p6', 'proj_test', 6, 'generate_artifact', 'pending', '{}')"
    )
    conn.commit()
    from src.backend.engine.workflow_engine import WorkflowEngine

    return WorkflowEngine(conn=conn)


class TestPhase6SuccessPath:
    def test_phase6_success_path_sets_succeeded(self, engine):
        agent = MagicMock()
        agent.produce_sfx.return_value = [
            {"sfx_id": "sfx_001", "type": "boom", "timestamp_seconds": 1.0},
        ]
        agent.check_sparsity.return_value = {
            "verdict": "PASS",
            "rule": "sparsity",
        }

        with patch("src.backend.workers.tasks.SFXAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase6_sfx_layout

                run_phase6_sfx_layout.call_local(
                    "task_p6",
                    {
                        "timeline": {
                            "segments": [
                                {
                                    "segment_id": "s1",
                                    "start_sec": 0.0,
                                    "content": "test",
                                }
                            ]
                        }
                    },
                )

        task = engine.get_task("task_p6")
        assert task is not None
        assert task["status"] == "succeeded"


class TestPhase6FailurePath:
    def test_phase6_failure_path_sets_failed(self, engine):
        agent = MagicMock()
        agent.produce_sfx.side_effect = RuntimeError("SFX generation failed")

        with patch("src.backend.workers.tasks.SFXAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase6_sfx_layout

                with pytest.raises(RuntimeError, match="SFX generation failed"):
                    run_phase6_sfx_layout.call_local(
                        "task_p6", {"timeline": {"segments": []}}
                    )

        task = engine.get_task("task_p6")
        assert task is not None
        assert task["status"] == "failed"


class TestPhase6ParamsForwarded:
    def test_phase6_params_forwarded_to_agent(self, engine):
        agent = MagicMock()
        agent.produce_sfx.return_value = [
            {"sfx_id": "sfx_001", "type": "boom", "timestamp_seconds": 1.0},
        ]
        agent.check_sparsity.return_value = {
            "verdict": "PASS",
            "rule": "sparsity",
        }

        timeline = {
            "segments": [{"segment_id": "s1", "start_sec": 0.0, "content": "test"}]
        }

        with patch("src.backend.workers.tasks.SFXAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase6_sfx_layout

                run_phase6_sfx_layout.call_local("task_p6", {"timeline": timeline})

        agent.produce_sfx.assert_called_once_with(timeline=timeline)
        agent.check_sparsity.assert_called_once()
