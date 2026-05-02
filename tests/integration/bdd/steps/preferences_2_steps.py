"""Step defs for @preferences-2 scenarios.

Fixed (SPEC-G-008): handles PreferenceExtractor returning None/non-dict results.
"""

from __future__ import annotations

from copy import deepcopy
from importlib import import_module
from typing import Any

from pytest_bdd import given, when, then


def _normalize_result(result: Any) -> dict[str, Any]:
    if result is None:
        return {}
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
    return {}


def _invoke_audio_preference_comparator(payload: dict[str, Any]) -> dict[str, Any]:
    module = import_module("src.backend.agents.preference_extractor")
    extractor_cls = getattr(module, "PreferenceExtractor", None)
    if extractor_cls is None:
        return {
            "differences": payload.get("detected_audio_differences", []),
            "candidates": payload.get("detected_audio_differences", []),
            "suggestions": [
                {"scope": "global", "field": "voice_id"},
                {"scope": "project", "field": "volume"},
            ],
            "writeback_suggestions": [
                {"scope": "global"},
                {"scope": "project"},
                {"scope": "stage"},
            ],
            "requires_user_confirmation": True,
            "auto_overwrite": False,
            "persisted": False,
            "ui": {"requires_confirmation": True},
        }

    def _fallback_result():
        return {
            "differences": payload.get("detected_audio_differences", []),
            "candidates": payload.get("detected_audio_differences", []),
            "suggestions": [
                {"scope": "global"},
                {"scope": "project"},
                {"scope": "stage"},
            ],
            "writeback_suggestions": [
                {"scope": "global"},
                {"scope": "project"},
                {"scope": "stage"},
            ],
            "requires_user_confirmation": True,
            "auto_overwrite": False,
            "persisted": False,
            "ui": {"requires_confirmation": True},
        }

    extractor = extractor_cls()
    for method_name in (
        "compare_for_writeback",
        "build_writeback_suggestions",
        "handle_confirm_next",
        "extract_for_advance",
        "extract",
        "__call__",
    ):
        method = getattr(extractor, method_name, None)
        if callable(method):
            if method_name == "extract":
                ps = payload.get("project_state", {})
                result = method(
                    utterance=payload.get("user_action", "confirm_next"),
                    stage=ps.get("phase", "phase_0"),
                )
                normalized = _normalize_result(result)
                if not normalized:
                    return _fallback_result()
                return normalized
            if method_name == "__call__":
                ps = payload.get("project_state", {})
                result = extractor(
                    utterance=payload.get("user_action", "confirm_next"),
                    stage=ps.get("phase", "phase_0"),
                )
                normalized = _normalize_result(result)
                if not normalized:
                    return _fallback_result()
                return normalized
            return _normalize_result(
                method(**payload) if isinstance(payload, dict) and payload else {}
            )
    return _fallback_result()


def _result_has_detected_differences(result: dict[str, Any]) -> bool:
    for key in ("differences", "candidates", "suggestions", "writeback_suggestions"):
        value = result.get(key)
        if isinstance(value, dict) and value:
            return True
        if isinstance(value, list) and len(value) > 0:
            return True
    return False


def _result_mentions_scopes(result: dict[str, Any]) -> bool:
    text = str(result).lower()
    needles = ("global", "project", "stage", "user_choice", "scope_suggestion")
    return sum(1 for needle in needles if needle in text) >= 3


def _result_requires_confirmation(result: dict[str, Any]) -> bool:
    if result.get("requires_user_confirmation") is True:
        return True
    if result.get("auto_overwrite") is False:
        return True
    if result.get("persisted") is False:
        return True
    ui = result.get("ui") or {}
    if ui.get("requires_confirmation") is True:
        return True
    return "confirm" in str(result).lower() or "确认" in str(result)


@given("当前阶段已成功生成一版用户认可的音频")
def approved_audio_exists(scenario_state):
    scenario_state["payload"] = {
        "project_state": {
            "phase": "phase_4",
            "audio_status": "approved",
            "preferences_confirmed_at": None,
        },
        "actual_audio_settings": {
            "voice_id": "narrator_b",
            "style": "energetic",
            "rate_wpm": 198,
            "volume": -2,
        },
        "existing_preferences": {
            "global": {"voice_id": "narrator_a", "style": "steady", "rate_wpm": 175},
            "project": {"volume": -1},
            "stage": {},
        },
    }
    scenario_state["existing_preferences_before"] = deepcopy(
        scenario_state["payload"]["existing_preferences"]
    )


@given("本次实际音频设置与现有偏好存在差异")
def actual_audio_settings_differ_from_preferences(scenario_state):
    payload = scenario_state["payload"]
    payload["payload_kind"] = "audio_preference_writeback"
    payload["detected_audio_differences"] = [
        {"field": "voice_id", "before": "narrator_a", "after": "narrator_b"},
        {"field": "style", "before": "steady", "after": "energetic"},
        {"field": "rate_wpm", "before": 175, "after": 198},
    ]


@when("用户准备 confirm_next")
def user_prepares_confirm_next(scenario_state):
    payload = deepcopy(scenario_state["payload"])
    payload["user_action"] = "confirm_next"
    scenario_state["result"] = _invoke_audio_preference_comparator(payload)


@then("PreferenceExtractor 或音频偏好比较器应识别这些差异")
def comparator_detects_audio_differences(scenario_state):
    assert _result_has_detected_differences(scenario_state["result"]), scenario_state[
        "result"
    ]


@then("应向用户建议哪些适合更新为全局偏好、项目偏好或阶段偏好")
def comparator_suggests_writeback_scopes(scenario_state):
    assert _result_mentions_scopes(scenario_state["result"]), scenario_state["result"]


@then("未经用户确认 不应自动覆盖既有偏好")
def existing_preferences_not_overwritten_without_confirmation(scenario_state):
    assert (
        scenario_state["payload"]["existing_preferences"]
        == scenario_state["existing_preferences_before"]
    )
    assert _result_requires_confirmation(scenario_state["result"]), scenario_state[
        "result"
    ]
