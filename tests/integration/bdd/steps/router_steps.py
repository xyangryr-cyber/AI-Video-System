"""Step defs for @router scenarios.

Scenarios covered here (growing list):
  * Router 超时或 JSON 解析失败时回退 clarify
"""

from __future__ import annotations

from pytest_bdd import given, when, then, parsers


@given("Router 模型调用超时或返回非 JSON 文本")
def router_returns_garbage(scenario_state):
    scenario_state["raw_router_output"] = "<<<timeout/garbage>>>"


@when("API 层尝试解析 Router 输出")
def api_parses_output(scenario_state, sut_router):
    raw = scenario_state["raw_router_output"]
    scenario_state["result"] = sut_router.parse_or_fallback(raw)


@then("系统应回退为 clarify")
def assert_action_is_clarify(scenario_state):
    assert scenario_state["result"]["action"] == "clarify"


@then("不应猜测用户意图")
def assert_no_guessing(scenario_state):
    result = scenario_state["result"]
    # A guessed intent would leak into params.scope or params.target.
    # Fallback path must leave params empty or contain only diagnostic keys.
    params = result.get("params") or {}
    assert not params.get("scope")
    assert not params.get("target")


@then(parsers.parse("events 中应记录 {event_name} 或等价事件"))
def assert_event_logged(scenario_state, event_name):
    events = scenario_state["result"].get("events") or []
    # Match either the exact name or a dotted-prefix equivalent.
    prefix = event_name.split()[0]  # "router.intent_fallback"
    assert any(e.get("type", "").startswith(prefix) for e in events), (
        f"no event matching {event_name!r} in {events!r}"
    )
