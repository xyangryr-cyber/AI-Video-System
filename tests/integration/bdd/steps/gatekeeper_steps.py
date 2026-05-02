"""Step defs for @gatekeeper scenarios."""

from __future__ import annotations

import json
from typing import Any

from pytest_bdd import given, then


def _ensure_project_phase(
    db: Any, project_id: str, phase_num: int, **phase_overrides: Any
) -> None:
    db.execute(
        "INSERT OR IGNORE INTO projects(project_id, title, description, current_phase) "
        "VALUES(?, ?, ?, ?)",
        (project_id, "BDD Gate Test", "BDD", phase_num),
    )
    db.execute(
        "INSERT OR IGNORE INTO phases(project_id, phase_num, phase_name, artifact_path, "
        "artifact_status, preferences_confirmed_at) VALUES(?, ?, ?, ?, ?, ?)",
        (
            project_id,
            phase_num,
            f"P{phase_num}",
            phase_overrides.get("artifact_path"),
            phase_overrides.get("artifact_status"),
            phase_overrides.get("preferences_confirmed_at"),
        ),
    )
    db.commit()


def _ensure_phase_updated(
    db: Any, project_id: str, phase_num: int, **fields: Any
) -> None:
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [project_id, phase_num]
    db.execute(
        f"UPDATE phases SET {set_clause} WHERE project_id = ? AND phase_num = ?",
        values,
    )
    db.commit()


def _base_project_state() -> dict[str, Any]:
    return {
        "current_phase": "phase_3",
        "artifact_exists": False,
        "artifact_ref": None,
        "review_verdict": "FAIL",
        "task_ledger_statuses": [],
        "async_task_statuses": [],
        "preferences_confirmed_at": None,
        "phase_status": "active",
        "skip_phase_allowed": False,
    }


def _allow_value(result: dict[str, Any]) -> Any:
    return (
        result.get("passed")
        if "passed" in result
        else result.get("allow_advance")
        if "allow_advance" in result
        else result.get("allowed")
        if "allowed" in result
        else result.get("ok")
    )


def _next_phase_value(result: dict[str, Any]) -> Any:
    if "next_phase" in result:
        return result["next_phase"]
    transition = result.get("transition")
    if isinstance(transition, dict) and "next_phase" in transition:
        return transition["next_phase"]
    return result.get("advanced_to")


def _failure_text(result: dict[str, Any]) -> str:
    value = (
        result.get("failure_reasons")
        or result.get("failed_checks")
        or result.get("errors")
        or result
    )
    return str(value)


def _checked_items_text(result: dict[str, Any]) -> str:
    value = (
        result.get("checked_items")
        or result.get("passed_checks")
        or result.get("failed_checks")
        or []
    )
    return str(value)


# -- Scenario 1: all gates pass -------------------------------------------


@given("当前阶段主产物存在且非空")
def current_phase_artifact_exists(scenario_state, bdd_db_conn):
    state = _base_project_state()
    state["artifact_exists"] = True
    state["artifact_ref"] = "artifacts/phase_3/output.json"
    state["project_id"] = "proj-bdd-gate-1"
    scenario_state["gatekeeper_payload"] = {"project_state": state}
    _ensure_project_phase(
        bdd_db_conn,
        state["project_id"],
        3,
        artifact_path=state["artifact_ref"],
        artifact_status="ok",
        preferences_confirmed_at=None,
    )


@given("当前阶段最新 review verdict 为 PASS")
def latest_review_pass(scenario_state, bdd_db_conn):
    state = scenario_state.setdefault(
        "gatekeeper_payload", {"project_state": _base_project_state()}
    )["project_state"]
    state["review_verdict"] = "PASS"
    project_id = state.setdefault("project_id", "proj-bdd-gate-1")
    phase_num = 3
    _ensure_project_phase(
        bdd_db_conn,
        project_id,
        phase_num,
        artifact_path=state.get("artifact_ref"),
        artifact_status="ok",
        preferences_confirmed_at=state.get("preferences_confirmed_at"),
    )
    bdd_db_conn.execute(
        "INSERT OR REPLACE INTO task_ledger(id, project_id, phase, type, status, "
        "target_version, result_ref, params) VALUES(?, ?, ?, 'review', 'succeeded', 0, ?, '{}')",
        (
            "task-review-pass",
            project_id,
            phase_num,
            json.dumps({"verdict": "PASS", "blocking_issues": []}),
        ),
    )
    bdd_db_conn.commit()


@given("task_ledger 中不存在 pending、queued、running、timeout 状态任务")
def no_inflight_task_ledger_tasks(scenario_state):
    state = scenario_state.setdefault(
        "gatekeeper_payload", {"project_state": _base_project_state()}
    )["project_state"]
    state["task_ledger_statuses"] = []


@given("async_tasks 中不存在 running 状态任务")
def no_running_async_tasks(scenario_state):
    state = scenario_state.setdefault(
        "gatekeeper_payload", {"project_state": _base_project_state()}
    )["project_state"]
    state["async_task_statuses"] = []


@given("当前阶段 preferences_confirmed_at 非空")
def preferences_confirmed(scenario_state, bdd_db_conn):
    state = scenario_state.setdefault(
        "gatekeeper_payload", {"project_state": _base_project_state()}
    )["project_state"]
    state["preferences_confirmed_at"] = "2026-04-18T00:00:00Z"
    project_id = state.get("project_id", "proj-bdd-gate-1")
    phase_num = 3
    _ensure_phase_updated(
        bdd_db_conn,
        project_id,
        phase_num,
        preferences_confirmed_at=state["preferences_confirmed_at"],
    )


# -- Then steps ------------------------------------------------------------


@then("GateKeeper.check 应返回通过")
def gatekeeper_check_passes(scenario_state):
    result = scenario_state["result"]
    assert _allow_value(result) is True, result


@then("FSM 应进入下一阶段")
def fsm_enters_next_phase(scenario_state):
    result = scenario_state["result"]
    assert _next_phase_value(result), result


@then("新阶段 task_ledger 应被初始化")
def next_phase_task_ledger_initialized(scenario_state):
    result = scenario_state["result"]
    initialized = result.get("task_ledger_initialized")
    if initialized is None:
        initialized = result.get("next_task_ledger") or result.get(
            "initialized_task_ledger"
        )
    assert initialized, result


# -- Scenario 2: review FAIL blocks advance --------------------------------


@given("当前阶段最新 review verdict 为 FAIL")
def latest_review_fail(scenario_state, bdd_db_conn):
    state = _base_project_state()
    state["review_verdict"] = "FAIL"
    state["artifact_exists"] = True
    state["artifact_ref"] = "artifacts/phase_3/output.json"
    state["preferences_confirmed_at"] = "2026-04-18T00:00:00Z"
    state["project_id"] = "proj-bdd-gate-2"
    scenario_state["gatekeeper_payload"] = {"project_state": state}
    _ensure_project_phase(
        bdd_db_conn,
        state["project_id"],
        3,
        artifact_path=state["artifact_ref"],
        artifact_status="ok",
        preferences_confirmed_at=state["preferences_confirmed_at"],
    )
    bdd_db_conn.execute(
        "INSERT OR REPLACE INTO task_ledger(id, project_id, phase, type, status, "
        "target_version, result_ref, params) VALUES(?, ?, ?, 'review', 'succeeded', 0, ?, '{}')",
        (
            "task-review-fail",
            state["project_id"],
            3,
            json.dumps({"verdict": "FAIL", "blocking_issues": ["审核未通过"]}),
        ),
    )
    bdd_db_conn.commit()


@then("GateKeeper.check 应返回失败")
def gatekeeper_check_fails(scenario_state):
    result = scenario_state["result"]
    assert _allow_value(result) is False, result


@then("failure_reasons 中应包含审核未通过原因")
def failure_reasons_include_review_failure(scenario_state):
    assert (
        "审核" in _failure_text(scenario_state["result"])
        or "review" in _failure_text(scenario_state["result"]).lower()
    )


@then("当前阶段不应推进")
def current_phase_does_not_advance(scenario_state):
    result = scenario_state["result"]
    next_phase = _next_phase_value(result)
    assert (
        not next_phase
        or next_phase
        == scenario_state["gatekeeper_payload"]["project_state"]["current_phase"]
    ), result


# -- Scenario 3: missing artifact blocks advance ---------------------------


@given("phases.current.artifact_ref 为空或指向文件不存在")
def artifact_missing(scenario_state, bdd_db_conn):
    state = _base_project_state()
    state["review_verdict"] = "PASS"
    state["artifact_exists"] = False
    state["artifact_ref"] = None
    state["preferences_confirmed_at"] = "2026-04-18T00:00:00Z"
    state["project_id"] = "proj-bdd-gate-3"
    scenario_state["gatekeeper_payload"] = {"project_state": state}
    _ensure_project_phase(
        bdd_db_conn,
        state["project_id"],
        3,
        artifact_path=None,
        artifact_status=None,
        preferences_confirmed_at=state["preferences_confirmed_at"],
    )
    bdd_db_conn.execute(
        "INSERT OR REPLACE INTO task_ledger(id, project_id, phase, type, status, "
        "target_version, result_ref, params) VALUES(?, ?, ?, 'review', 'succeeded', 0, ?, '{}')",
        (
            "task-review-pass-3",
            state["project_id"],
            3,
            json.dumps({"verdict": "PASS", "blocking_issues": []}),
        ),
    )
    bdd_db_conn.commit()


@then("failure_reasons 中应包含“主产物生成失败”或等价原因")
def failure_reasons_include_artifact_failure(scenario_state):
    text = _failure_text(scenario_state["result"])
    assert "主产物" in text or "artifact" in text.lower(), text


# -- Scenario 4: running async task blocks advance -------------------------


@given("当前阶段存在 async_task.status=running")
def running_async_task_exists(scenario_state, bdd_db_conn):
    state = _base_project_state()
    state["artifact_exists"] = True
    state["artifact_ref"] = "artifacts/phase_3/output.json"
    state["review_verdict"] = "PASS"
    state["async_task_statuses"] = ["running"]
    state["preferences_confirmed_at"] = "2026-04-18T00:00:00Z"
    state["project_id"] = "proj-bdd-gate-4"
    scenario_state["gatekeeper_payload"] = {"project_state": state}
    _ensure_project_phase(
        bdd_db_conn,
        state["project_id"],
        3,
        artifact_path=state["artifact_ref"],
        artifact_status="ok",
        preferences_confirmed_at=state["preferences_confirmed_at"],
    )
    bdd_db_conn.execute(
        "INSERT OR REPLACE INTO task_ledger(id, project_id, phase, type, status, "
        "target_version, result_ref, params) VALUES(?, ?, ?, 'review', 'succeeded', 0, ?, '{}')",
        (
            "task-review-pass-4",
            state["project_id"],
            3,
            json.dumps({"verdict": "PASS", "blocking_issues": []}),
        ),
    )
    bdd_db_conn.execute(
        "INSERT OR IGNORE INTO async_tasks(task_id, project_id, phase, type, status, params) "
        "VALUES('async-running', ?, ?, 'tts', 'running', '{}')",
        (state["project_id"], 3),
    )
    bdd_db_conn.commit()


@then("failure_reasons 中应包含“无进行中异步任务”未满足")
def failure_reasons_include_async_failure(scenario_state):
    text = _failure_text(scenario_state["result"])
    assert "异步" in text or "async" in text.lower(), text


# -- Scenario 5: skip phase gate branch ------------------------------------


@given("当前阶段允许 skip_phase")
def current_phase_allows_skip(scenario_state, bdd_db_conn):
    state = _base_project_state()
    state["skip_phase_allowed"] = True
    state["project_id"] = "proj-bdd-gate-5"
    scenario_state["gatekeeper_payload"] = {"project_state": state, "mode": "skip"}
    _ensure_project_phase(
        bdd_db_conn,
        state["project_id"],
        3,
        artifact_path=None,
        artifact_status=None,
        preferences_confirmed_at=None,
    )


@given("phases.current.status 已标记为 skipped")
def phase_marked_skipped(scenario_state):
    state = scenario_state.setdefault(
        "gatekeeper_payload", {"project_state": _base_project_state()}
    )["project_state"]
    state["phase_status"] = "skipped"


@given("没有进行中任务")
def no_inflight_tasks_for_skip(scenario_state):
    state = scenario_state.setdefault(
        "gatekeeper_payload", {"project_state": _base_project_state()}
    )["project_state"]
    state["task_ledger_statuses"] = []
    state["async_task_statuses"] = []


@then("GateKeeper.check 应按跳过分支通过")
def skip_branch_passes(scenario_state):
    result = scenario_state["result"]
    assert _allow_value(result) is True, result


@then("不要求当前阶段生成主产物或 review PASS")
def skip_branch_does_not_require_artifact_or_review(scenario_state):
    result = scenario_state["result"]
    checked_items = _checked_items_text(result).lower()
    if checked_items:
        assert "artifact" not in checked_items
        assert "review" not in checked_items
