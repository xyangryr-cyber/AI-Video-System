"""[SPEC-G-000d] Phase 11 task routing tests -- FinalCutAgent.

AC-11.1: success path → task_ledger.status = succeeded
AC-11.2: failure path → task_ledger.status = failed, error_code = AGENT_FAILURE
AC-11.3: params forwarded to agent methods
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
        "VALUES('proj_test', 11, 'P11')"
    )
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type, status, params) "
        "VALUES('task_p11', 'proj_test', 11, 'generate_artifact', 'pending', '{}')"
    )
    conn.commit()
    from src.backend.engine.workflow_engine import WorkflowEngine

    return WorkflowEngine(conn=conn)


class TestPhase11SuccessPath:
    def test_phase11_success_path_sets_succeeded(self, engine):
        agent = MagicMock()
        agent.adjust.return_value = {
            "output_path": "phase_11/final_cut.mp4",
            "adjustments_applied": ["brightness"],
        }
        agent.run_audit_3.return_value = {
            "verdict": "PASS",
            "total_inconsistencies": 0,
        }

        with patch("src.backend.workers.tasks.FinalCutAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase11_final_cut

                run_phase11_final_cut.call_local(
                    "task_p11",
                    {
                        "rough_cut_path": "phase_10/rough_cut.mp4",
                        "adjustments": {"brightness": 1.1},
                        "audit_1": {"inconsistency_count": 0},
                        "audit_2": {"inconsistency_count": 0},
                    },
                )

        task = engine.get_task("task_p11")
        assert task is not None
        assert task["status"] == "succeeded"


class TestPhase11FailurePath:
    def test_phase11_failure_path_sets_failed(self, engine):
        agent = MagicMock()
        agent.adjust.side_effect = RuntimeError("Final cut adjustment failed")

        with patch("src.backend.workers.tasks.FinalCutAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase11_final_cut

                with pytest.raises(RuntimeError, match="Final cut adjustment failed"):
                    run_phase11_final_cut.call_local(
                        "task_p11",
                        {
                            "rough_cut_path": "phase_10/rough_cut.mp4",
                            "adjustments": {},
                            "audit_1": {},
                            "audit_2": {},
                        },
                    )

        task = engine.get_task("task_p11")
        assert task is not None
        assert task["status"] == "failed"


class TestPhase11ParamsForwarded:
    def test_phase11_params_forwarded_to_agent(self, engine):
        agent = MagicMock()
        agent.adjust.return_value = {
            "output_path": "phase_11/final_cut.mp4",
        }
        agent.run_audit_3.return_value = {
            "verdict": "PASS",
        }

        rough_cut_path = "phase_10/rough_cut.mp4"
        adjustments = {"brightness": 1.1, "contrast": 1.05}
        audit_1 = {"inconsistency_count": 0}
        audit_2 = {"inconsistency_count": 0}

        with patch("src.backend.workers.tasks.FinalCutAgent", return_value=agent):
            with patch(
                "src.backend.workers.tasks._get_workflow_engine",
                return_value=engine,
            ):
                from src.backend.workers.tasks import run_phase11_final_cut

                run_phase11_final_cut.call_local(
                    "task_p11",
                    {
                        "rough_cut_path": rough_cut_path,
                        "adjustments": adjustments,
                        "audit_1": audit_1,
                        "audit_2": audit_2,
                    },
                )

        agent.adjust.assert_called_once_with(
            rough_cut_path=rough_cut_path,
            adjustments=adjustments,
        )
        agent.run_audit_3.assert_called_once_with(
            audit_1=audit_1,
            audit_2=audit_2,
        )
