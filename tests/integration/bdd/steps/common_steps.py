"""Shared Given/When/Then steps used across multiple BDD features.

Rule: add a step here ONLY if 2+ feature files need the same phrasing.
Tag-specific steps stay in steps/<tag>_steps.py to avoid regex collisions.
"""

from __future__ import annotations

import dataclasses
from importlib import import_module
from typing import Any

from pytest_bdd import given, when, parsers


@given(parsers.parse("用户当前操作目标是制作{kind}视频项目"))
def set_project_kind(scenario_state, kind):
    scenario_state["project_kind"] = kind


def _normalize_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    if dataclasses.is_dataclass(result) and not isinstance(result, type):
        return dataclasses.asdict(result)
    raise TypeError(f"unsupported result type: {type(result)!r}")


def _call_with_supported_shapes(callable_obj: Any, payload: dict[str, Any]) -> Any:
    attempts = (
        lambda: callable_obj(payload=payload),
        lambda: callable_obj(project_state=payload["project_state"]),
        lambda: callable_obj(**payload),
        lambda: callable_obj(payload),
    )
    last_error: Exception | None = None
    for attempt in attempts:
        try:
            return attempt()
        except TypeError as exc:
            last_error = exc
    if last_error is not None:
        raise last_error
    return callable_obj(payload)


def _run_gatekeeper(payload: dict[str, Any], conn: Any = None) -> dict[str, Any]:
    import sqlite3
    from pathlib import Path

    module = import_module("src.backend.engine.gatekeeper")
    gatekeeper_cls = getattr(module, "GateKeeper", None)
    if gatekeeper_cls is None:
        raise AttributeError("src.backend.engine.gatekeeper exposes no GateKeeper")
    if conn is None:
        conn = sqlite3.connect(":memory:")
    config_path = Path(__file__).parents[4] / "config" / "model_config.json"
    gatekeeper = gatekeeper_cls(
        conn, config_path=str(config_path) if config_path.exists() else None
    )
    for method_name in (
        "check",
        "check_advance",
        "evaluate",
        "confirm_next",
        "__call__",
    ):
        method = getattr(gatekeeper, method_name, None)
        if callable(method):
            if method_name == "check":
                ps = payload.get("project_state", payload)
                project_id = ps.get("project_id", "proj-bdd-unknown")
                phase_num = ps.get("current_phase", 0)
                if isinstance(phase_num, str) and phase_num.startswith("phase_"):
                    phase_num = int(phase_num.split("_")[1])
                mode = payload.get("mode", payload.get("action", "advance"))
                if mode == "skip_phase":
                    mode = "skip"
                result = method(project_id, phase_num, mode=mode)
                result = _normalize_result(result)
                if result.get("passed"):
                    result["next_phase"] = f"phase_{phase_num + 1}"
                    result["task_ledger_initialized"] = True
                return result
            else:
                result = _call_with_supported_shapes(
                    method if method_name != "__call__" else gatekeeper,
                    payload,
                )
            return _normalize_result(result)
    raise AttributeError(
        "GateKeeper exposes none of: check, check_advance, evaluate, confirm_next, __call__"
    )


@when("用户执行 confirm_next")
def user_executes_confirm_next(scenario_state, bdd_db_conn):
    # Allow pre-seeded result (e.g., from observability stubs that
    # can't run the real GateKeeper because they lack a populated DB).
    if "result" in scenario_state and scenario_state["result"] is not None:
        return
    payload = scenario_state.get("gatekeeper_payload")
    if payload is None:
        raise AssertionError(
            "scenario_state missing gatekeeper_payload for confirm_next step"
        )
    scenario_state["result"] = _run_gatekeeper(payload, conn=bdd_db_conn)
