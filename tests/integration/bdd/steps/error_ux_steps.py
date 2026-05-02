"""Step defs for @error_ux scenarios."""

from __future__ import annotations

import re
from importlib import import_module
from pathlib import Path
from typing import Any

from pytest_bdd import given, when, then

_REPO_ROOT = Path(__file__).resolve().parents[4]
_ERROR_UX_MAP_PATH = _REPO_ROOT / "src/frontend/utils/errorUxMap.ts"
_ERROR_TOAST_PATH = _REPO_ROOT / "src/frontend/components/errors/ErrorToast.tsx"
_ERROR_MODAL_PATH = _REPO_ROOT / "src/frontend/components/errors/ErrorModal.tsx"
_USE_ERROR_HANDLER_PATH = _REPO_ROOT / "src/frontend/hooks/useErrorHandler.ts"


def _resolve_canonical_error_code(code: str) -> str:
    module = import_module("src.shared.constants.error_codes")
    for attr in ("resolve_error_code", "lookup_error_code", "normalize_error_code"):
        resolver = getattr(module, attr, None)
        if callable(resolver):
            resolved = resolver(code)
            if isinstance(resolved, str) and resolved:
                return resolved
    for attr in ("ERROR_CODE_ALIASES", "ERROR_CODES", "ERROR_CODE_REGISTRY"):
        registry = getattr(module, attr, None)
        if isinstance(registry, dict) and code in registry:
            value = registry[code]
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                for key in ("code", "error_code", "id"):
                    if isinstance(value.get(key), str):
                        return value[key]
    upper = code.upper()
    direct = getattr(module, upper, None)
    if isinstance(direct, str) and direct:
        return direct
    raise AttributeError(
        f"cannot resolve canonical error code for {code!r} from src.shared.constants.error_codes"
    )


def _extract_error_ux_entry(canonical_code: str) -> dict[str, Any]:
    source = _ERROR_UX_MAP_PATH.read_text()
    pattern = re.compile(
        rf'{re.escape(canonical_code)}:\s*\{{\s*tier:\s*"([^"]+)",\s*component:\s*"([^"]+)",\s*actions:\s*\[([^\]]*)\]',
        re.MULTILINE,
    )
    match = pattern.search(source)
    if not match:
        raise KeyError(f"{canonical_code} not found in {_ERROR_UX_MAP_PATH}")
    actions = [
        item.strip().strip('"') for item in match.group(3).split(",") if item.strip()
    ]
    return {
        "tier": match.group(1),
        "component": match.group(2),
        "actions": actions,
        "source": source,
        "toast_source": _ERROR_TOAST_PATH.read_text(),
        "modal_source": _ERROR_MODAL_PATH.read_text(),
        "handler_source": _USE_ERROR_HANDLER_PATH.read_text(),
    }


@given("系统错误码为 tts_api_timeout")
def error_code_tts_timeout(scenario_state):
    scenario_state["error_code"] = "tts_api_timeout"


@given("系统错误码为 financial_data_unavailable")
def error_code_financial_data_unavailable(scenario_state):
    scenario_state["error_code"] = "financial_data_unavailable"


@given("系统错误码为 worker_crash_max_retries")
def error_code_worker_crash_max_retries(scenario_state):
    scenario_state["error_code"] = "worker_crash_max_retries"


@when("错误映射表转换为用户提示")
def error_map_converts_to_user_prompt(scenario_state):
    canonical_code = _resolve_canonical_error_code(scenario_state["error_code"])
    scenario_state["canonical_code"] = canonical_code
    scenario_state["entry"] = _extract_error_ux_entry(canonical_code)


@then("level 应为 auto_handling")
def level_is_auto_handling(scenario_state):
    assert scenario_state["entry"]["tier"] == "auto_handling", scenario_state["entry"]


@then("前端应展示 toast 而不是阻塞模态框")
def frontend_shows_toast_not_blocking_modal(scenario_state):
    entry = scenario_state["entry"]
    assert entry["component"] == "toast", entry
    assert 'role="dialog"' not in entry["toast_source"]
    assert "toast.error" in entry["handler_source"]


@then("UI 中应显示预计自动恢复时间")
def ui_shows_eta(scenario_state):
    toast_source = scenario_state["entry"]["toast_source"]
    assert "ETA" in toast_source or "etaSec" in toast_source, toast_source


@then("level 应为 user_choice")
def level_is_user_choice(scenario_state):
    assert scenario_state["entry"]["tier"] == "user_choice", scenario_state["entry"]


@then("前端应展示模态框")
def frontend_shows_modal(scenario_state):
    entry = scenario_state["entry"]
    assert entry["component"] == "modal", entry
    assert 'role="dialog"' in entry["modal_source"]


@then("actions 应至少包含 manual_input 与 skip")
def actions_include_manual_input_and_skip(scenario_state):
    actions = set(scenario_state["entry"]["actions"])
    assert {"manual_input", "skip"}.issubset(actions), actions


@then("用户未选择前不应自动继续流程")
def no_auto_continue_before_user_choice(scenario_state):
    text = str(scenario_state["entry"]).lower()
    assert "auto_continue" not in text and "continue_immediately" not in text, text


@then("level 应为 user_action")
def level_is_user_action(scenario_state):
    assert scenario_state["entry"]["tier"] == "user_action", scenario_state["entry"]


@then("前端应展示红色强调的模态框")
def frontend_shows_red_emphasis_modal(scenario_state):
    modal_source = scenario_state["entry"]["modal_source"]
    assert "red" in modal_source.lower() or "danger" in modal_source.lower(), (
        modal_source
    )


@then("actions 应至少包含 retry 或 go_back")
def actions_include_retry_or_go_back(scenario_state):
    actions = set(scenario_state["entry"]["actions"])
    assert {"retry", "go_back"} & actions, actions
