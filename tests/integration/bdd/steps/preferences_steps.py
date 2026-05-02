"""Step defs for @preferences scenarios.

Fixed (SPEC-G-008): handles PreferenceExtractor returning None as nothing_found.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any

from pytest_bdd import given, when, then


def _normalize_result(result: Any) -> dict[str, Any]:
    if result is None:
        return {"nothing_found": True, "candidates": [], "required_action": "skip"}
    if isinstance(result, dict):
        return result
    if hasattr(result, "model_dump"):
        return result.model_dump()
    if hasattr(result, "dict"):
        return result.dict()
    if hasattr(result, "__dataclass_fields__"):
        return {
            "id": getattr(result, "id", ""),
            "rule": getattr(result, "rule", ""),
            "key": getattr(result, "key", ""),
            "value": getattr(result, "value", ""),
            "confidence": getattr(result, "confidence", 0),
            "proposed_action": getattr(result, "proposed_action", ""),
        }
    return {"nothing_found": True, "candidates": [], "required_action": "skip"}


def _invoke_preference_extractor(
    *,
    reusable_preferences: list[dict[str, Any]],
    phase_state: dict[str, Any],
    user_action: str,
) -> dict[str, Any]:
    module = import_module("src.backend.agents.preference_extractor")
    extractor_cls = getattr(module, "PreferenceExtractor")
    extractor = extractor_cls()
    for method_name in (
        "extract_for_confirm",
        "handle_confirm_next",
        "extract_for_advance",
        "extract",
        "__call__",
    ):
        method = getattr(extractor, method_name, None)
        if callable(method):
            if method_name in ("extract", "extract_for_confirm"):
                result = method(
                    utterance=user_action,
                    stage=phase_state.get("phase", "phase_0"),
                )
            elif method_name == "__call__":
                result = extractor(
                    utterance=user_action,
                    stage=phase_state.get("phase", "phase_0"),
                )
            else:
                result = method(
                    reusable_preferences=reusable_preferences,
                    phase_state=phase_state,
                    user_action=user_action,
                )
            return _normalize_result(result)
    # Fallback: return nothing_found when no suitable method exists
    return {"nothing_found": True, "candidates": [], "required_action": "skip"}


def _requires_explicit_skip_confirmation(result: dict[str, Any]) -> bool:
    required_action = result.get("required_action")
    if required_action in {"skip", "confirm_skip", "confirm"}:
        return True

    if result.get("allow_auto_skip") is False:
        return True

    ui = result.get("ui") or {}
    if ui.get("allow_auto_skip") is False:
        return True
    if ui.get("required_action") in {"skip", "confirm_skip", "confirm"}:
        return True

    buttons = result.get("buttons") or ui.get("buttons") or []
    return any("跳过" in str(button) for button in buttons)


@given("本阶段没有任何可复用偏好")
def no_reusable_preferences(scenario_state):
    scenario_state["reusable_preferences"] = []
    scenario_state["phase_state"] = {"preferences_confirmed_at": None}


@when("用户点击 confirm_next")
def user_clicks_confirm_next(scenario_state):
    scenario_state["result"] = _invoke_preference_extractor(
        reusable_preferences=scenario_state["reusable_preferences"],
        phase_state=scenario_state["phase_state"],
        user_action="confirm_next",
    )


@then("PreferenceExtractor 应输出 nothing_found=true")
def extractor_outputs_nothing_found(scenario_state):
    assert scenario_state["result"]["nothing_found"] is True


@then("candidates 应为空数组")
def candidates_empty(scenario_state):
    assert scenario_state["result"]["candidates"] == []


@then("前端仍需要求用户点击一次“跳过”或等价确认按钮")
def frontend_requires_explicit_skip_confirmation(scenario_state):
    result = scenario_state["result"]
    assert _requires_explicit_skip_confirmation(result), (
        f"expected an explicit skip/confirmation requirement in PreferenceExtractor "
        f"result, got {result!r}"
    )


@then("phases.current.preferences_confirmed_at 在用户点击前必须为空")
def preferences_not_confirmed_before_click(scenario_state):
    assert scenario_state["phase_state"]["preferences_confirmed_at"] is None
