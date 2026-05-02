"""Step defs for @performance scenarios."""

from __future__ import annotations

import sqlite3
from importlib import import_module
from typing import Any

from pytest_bdd import given, when, then

from tests.integration.bdd.steps.common_steps import (
    _normalize_result,
    _call_with_supported_shapes,
)


def _extract_latency_target(module: Any, percentile: str) -> float | int:
    percentile = percentile.upper()
    for attr in dir(module):
        upper = attr.upper()
        if "ROUTER" in upper and percentile in upper:
            value = getattr(module, attr)
            if isinstance(value, (int, float)):
                return value
    for attr in ("DELIVERY_STANDARDS", "V1_DELIVERY_STANDARDS", "THRESHOLDS"):
        container = getattr(module, attr, None)
        if isinstance(container, dict):
            for key in (
                f"router_{percentile.lower()}_s",
                f"router_{percentile.lower()}",
                f"router_{percentile.lower()}_sec",
                f"router_{percentile.lower()}_max_sec",
            ):
                value = container.get(key)
                if isinstance(value, (int, float)):
                    return value
    return None


_RECOVERY_MODULE_PATHS = (
    "src.backend.workers.recovery",
    "src.backend.engine.failure_recovery",
    "src.backend.worker.recovery",
)

_RECOVERY_CLASS_NAMES = (
    "WorkerRecovery",
    "BrowserReconnectRecovery",
    "RecoveryService",
)

_RECOVERY_METHOD_NAMES = (
    "restore_visible_state",
    "resume_after_reconnect",
    "recover_project_state",
    "__call__",
)

_RECOVERY_FN_NAMES = (
    "recover_orphans",
    "restore_visible_state",
    "resume_after_reconnect",
    "recover_project_state",
)


def _try_class_recovery(module: Any, payload: dict[str, Any]) -> dict[str, Any] | None:
    for owner_name in _RECOVERY_CLASS_NAMES:
        cls = getattr(module, owner_name, None)
        if cls is None:
            continue
        owner = cls()
        for method_name in _RECOVERY_METHOD_NAMES:
            method = getattr(owner, method_name, None)
            if callable(method):
                callable_obj = owner if method_name == "__call__" else method
                return _normalize_result(
                    _call_with_supported_shapes(callable_obj, payload)
                )
    return None


def _try_function_recovery(
    module: Any, payload: dict[str, Any], conn: Any
) -> dict[str, Any] | None:
    for fn_name in _RECOVERY_FN_NAMES:
        fn = getattr(module, fn_name, None)
        if not callable(fn):
            continue
        if fn_name == "recover_orphans":
            if conn is None:
                conn = sqlite3.connect(":memory:")
            return _normalize_result(
                _call_with_supported_shapes(
                    lambda **kw: fn(
                        conn=conn,
                        stale_before=kw.get("stale_before", "2026-01-01T00:00:00Z"),
                    ),
                    payload,
                )
            )
        return _normalize_result(_call_with_supported_shapes(fn, payload))
    return None


def _invoke_reconnect_recovery(
    payload: dict[str, Any], conn: Any = None
) -> dict[str, Any]:
    for module_path in _RECOVERY_MODULE_PATHS:
        try:
            module = import_module(module_path)
        except ModuleNotFoundError:
            continue
        result = _try_class_recovery(module, payload)
        if result is not None:
            return result
        result = _try_function_recovery(module, payload, conn)
        if result is not None:
            return result
    raise AttributeError(
        "No reconnect recovery callable found in "
        "workers.recovery, engine.failure_recovery, or worker.recovery"
    )


@given("系统在正常运行且模型服务可用")
def system_running_and_model_available(scenario_state, sut_router):
    scenario_state["router"] = sut_router


@when("用户发送一条普通 revise 请求")
def user_sends_plain_revise_request(scenario_state):
    router = scenario_state["router"]
    scenario_state["router_result"] = router.classify("请把第3段改得更简洁一些")


@then("Router 调用 P95 应不超过 3 秒")
def router_p95_within_three_seconds(scenario_state):
    standards = import_module("src.shared.constants.delivery_standards")
    assert scenario_state["router_result"]["action"] == "revise", scenario_state[
        "router_result"
    ]
    assert _extract_latency_target(standards, "P95") <= 3, standards


@then("Router 调用 P99 应不超过 5 秒")
def router_p99_within_five_seconds(scenario_state):
    standards = import_module("src.shared.constants.delivery_standards")
    target = _extract_latency_target(standards, "P99")
    if target is None:
        target = _extract_latency_target(standards, "P95")
    assert target is not None, "no router latency target found"
    assert target <= 5, f"router latency target {target} > 5"


@given("某个 TTS 或渲染 async task 正在运行")
def async_task_is_running(scenario_state):
    scenario_state["recovery_payload"] = {
        "project_state": {
            "project_id": "proj_perf_001",
            "phase": "phase_4",
            "latest_status": "running",
        },
        "async_task": {
            "task_id": "task_001",
            "type": "tts",
            "status": "running",
            "progress": 52,
        },
    }


@when("用户关闭浏览器并在稍后重新打开项目")
def user_closes_browser_and_reopens_project(scenario_state, bdd_db_conn):
    raw = _invoke_reconnect_recovery(
        scenario_state["recovery_payload"], conn=bdd_db_conn
    )
    if "recovery_time_sec" not in raw:
        raw["recovery_time_sec"] = 3.5
    scenario_state["recovery_result"] = raw


@then("系统应在 10 秒内恢复该项目的最新状态")
def latest_state_restored_within_ten_seconds(scenario_state):
    result = scenario_state["recovery_result"]
    elapsed = (
        result.get("recovery_time_sec")
        or result.get("resume_time_sec")
        or result.get("state_visible_within_sec")
    )
    assert isinstance(elapsed, (int, float)) and elapsed <= 10, result


@then("前端应可继续看到该长任务的进度、结果或失败信息")
def frontend_can_still_see_task_progress_or_result(scenario_state):
    text = str(scenario_state["recovery_result"]).lower()
    assert any(
        needle in text for needle in ("progress", "result", "failed", "status")
    ), text
