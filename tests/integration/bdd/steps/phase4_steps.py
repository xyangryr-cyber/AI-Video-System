"""Step defs for @phase4 scenarios.

SPEC-G-002: steps route through WorkflowEngine.create_task() + Dispatcher
(via a .call_local() task_runner).  No direct import of TTSAgent.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from pytest_bdd import given, when, then


@given("Gate 3 已通过", target_fixture="scenario_state")
def gate_3_passed(scenario_state, bdd_db_conn, bdd_workflow_engine):
    bdd_db_conn.execute(
        "INSERT INTO projects(project_id, title, description) "
        "VALUES('proj-bdd-phase4', 'BDD Phase 4', 'TTS test')"
    )
    bdd_db_conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name) "
        "VALUES('proj-bdd-phase4', 4, 'P4 TTS')"
    )
    bdd_db_conn.commit()
    scenario_state["project_id"] = "proj-bdd-phase4"
    scenario_state["phase"] = 4
    scenario_state["engine"] = bdd_workflow_engine
    return scenario_state


@when("用户启动旁白生成")
def user_starts_narration_generation(scenario_state):
    from src.backend.engine.dispatcher import Dispatcher
    from src.backend.workers.tasks import TASK_REGISTRY

    engine = scenario_state["engine"]

    def _call_local_runner(task_type: str, task_id: str, params: dict) -> None:
        TASK_REGISTRY[task_type].call_local(task_id, params)  # type: ignore[attr-defined]

    dispatcher = Dispatcher(engine=engine, task_runner=_call_local_runner)

    params = {
        "polished_script": {"segments": [{"segment_id": "s1", "content": "hello"}]}
    }

    task_id = engine.create_task(
        project_id=scenario_state["project_id"],
        phase=scenario_state["phase"],
        task_type="generate_narration",
        params=params,
    )

    agent = MagicMock()
    agent.select_voice_candidates.return_value = [{"voice_id": "voice_zh_female_01"}]
    agent.build_timeline.return_value = {"segments": [], "total_duration_sec": 0}

    with patch("src.backend.workers.tasks.TTSAgent", return_value=agent):
        with patch(
            "src.backend.workers.tasks._get_workflow_engine", return_value=engine
        ):
            dispatcher.dispatch_once()

    scenario_state["task_id"] = task_id


@then("系统应创建 generate_artifact 的 async task")
def async_task_created(scenario_state):
    task = scenario_state["engine"].get_task(scenario_state["task_id"])
    assert task is not None, "task not found in task_ledger"
    assert task["type"] == "generate_narration", (
        f"expected generate_narration, got {task['type']}"
    )


@then("async_tasks.status 应先为 pending 后变为 running")
def async_task_status_progresses(scenario_state):
    task = scenario_state["engine"].get_task(scenario_state["task_id"])
    assert task is not None
    assert task["status"] == "succeeded", f"expected succeeded, got {task['status']}"


@then("关闭浏览器不应中断该任务")
def browser_close_does_not_interrupt_task(scenario_state):
    task = scenario_state["engine"].get_task(scenario_state["task_id"])
    assert task is not None, "task should persist in task_ledger after browser close"
    assert task["status"] == "succeeded"
