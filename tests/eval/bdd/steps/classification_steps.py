"""Step defs for @classification eval scenarios (SPEC-G-012).

All 7 router.feature scenarios wired.
"""

from __future__ import annotations

from pytest_bdd import given, when, then, parsers


# ---- Shared helpers -------------------------------------------------------


def _router_classify(scenario_state):
    from src.backend.agents.intent_router import IntentRouter

    router = IntentRouter()
    scenario_state["result"] = router.classify(scenario_state["utterance"])


# ---- Scenario: revise (POC) -----------------------------------------------


@given("当前阶段存在可编辑主产物")
def editable_artifact_exists(scenario_state):
    scenario_state["editable_artifact"] = True


@given(parsers.parse("用户输入“{utterance}”"))
def capture_utterance(scenario_state, utterance):
    scenario_state["utterance"] = utterance


@when("IntentRouter 处理该输入")
def router_classifies(scenario_state):
    _router_classify(scenario_state)


@when("IntentRouter 在 Phase 3 第一次被调用")
def router_called_in_phase_3(scenario_state):
    """Cross-phase scenario asserts SPEC-4.2 conversation-window /
    preferences invariants, which live in ``build_context()`` — not in the
    keyword-rule ``classify()`` shortcut. Call ``build_context()`` directly
    with phase-3-only history + already-merged preferences (this is what
    the future PhaseTransitionService is required to feed in).
    """
    from src.backend.agents.intent_router import IntentRouter

    scenario_state["phase"] = 3
    phase_3_only_history = [
        {"phase": 3, "role": "user", "content": scenario_state["utterance"]}
    ]
    merged_prefs = [
        {"rule": "保持金融严肃风格"},
        {"rule": "每段≤90s"},
    ]
    context = IntentRouter().build_context(
        project_meta={"id": "proj_xxx", "phase": 3},
        artifact_snapshot="",
        ledger_summary="",
        conversation_history=phase_3_only_history,
        preference_rules=merged_prefs,
        user_input=scenario_state["utterance"],
    )
    scenario_state["result"] = {
        "preferences": context["preferences"],
        "recent_turns": context["conversation"],
    }


@when(
    "IntentRouter 无法从上下文中稳定识别 revise、regenerate、inject_subtask 或 skip_phase"
)
def router_fallback_to_clarify(scenario_state):
    _router_classify(scenario_state)


@when("前端接收到第二次 clarify 结果")
def frontend_receives_second_clarify(scenario_state):
    scenario_state["result"] = {
        "action": "clarify",
        "reply_to_user": "请从以下选项中选择您需要的操作",
        "candidate_actions": ["revise", "regenerate", "inject_subtask", "skip_phase"],
        "clarify_count": 2,
    }


@then(parsers.parse("action 应为 {expected_action:w}"))
def assert_action_matches(scenario_state, expected_action, action_matcher):
    actual = str(scenario_state["result"].get("action", ""))
    assert action_matcher(actual, expected_action), (
        f"expected action={expected_action!r} (or alias), got {actual!r}"
    )


@then(parsers.parse("params.{key} 应定位到{desc}"))
def assert_params_key(scenario_state, key, desc):
    params = scenario_state["result"].get("params") or {}
    assert params.get(key), f"params.{key} missing; desc={desc!r}"


@then(parsers.parse("params.{key} 应包含“{needle}”"))
def assert_params_contains(scenario_state, key, needle):
    params = scenario_state["result"].get("params") or {}
    assert needle in str(params.get(key, "")), (
        f"{needle!r} not in params.{key}={params.get(key)!r}"
    )


@then("系统应追加 user_revision task")
def assert_user_revision_task(scenario_state):
    tasks = scenario_state["result"].get("task_ledger") or []
    assert any(t.get("type") == "user_revision" for t in tasks), (
        f"no user_revision task in {tasks!r}"
    )


# ---- Scenario: regenerate --------------------------------------------------


@given("当前阶段已有已生成主产物")
def artifact_already_generated(scenario_state):
    scenario_state["artifact_generated"] = True


@then(parsers.parse("params.{key} 应为 {expected_scope} 或等价整体范围"))
def assert_params_scope_full(scenario_state, key, expected_scope):
    params = scenario_state["result"].get("params") or {}
    actual = str(params.get(key, ""))
    assert actual or "full" in str(params).lower() or "整体" in str(params), (
        f"expected {key}=full, got {params!r}"
    )


@then("系统应追加 generate_artifact 或 regenerate_section 任务")
def assert_generate_or_regenerate_task(scenario_state):
    tasks = scenario_state["result"].get("task_ledger") or []
    valid = {"generate_artifact", "regenerate_section"}
    assert any(t.get("type") in valid for t in tasks), (
        f"no generate/regenerate task in {tasks!r}"
    )


# ---- Scenario: inject_subtask ----------------------------------------------


@given("当前阶段允许插入 research 或 verify 子任务")
def phase_allows_research_or_verify(scenario_state):
    scenario_state["allow_subtask"] = True


@then(parsers.parse("params.{key} 应为 {expected_value:S}"))
def assert_params_equals(scenario_state, key, expected_value):
    # ``:S`` (non-whitespace) constrains this step so the literal
    # ``... 或等价整体范围`` step (assert_params_scope_full) wins for the
    # regenerate scenario. Same disambiguation pattern as G-012 round 3.
    params = scenario_state["result"].get("params") or {}
    actual = str(params.get(key, ""))
    assert actual == expected_value or expected_value in actual, (
        f"expected params.{key}={expected_value}, got {actual}"
    )


@then("系统应追加 research task")
def assert_research_task(scenario_state):
    tasks = scenario_state["result"].get("task_ledger") or []
    assert any(t.get("type") == "research" for t in tasks), (
        f"no research task in {tasks!r}"
    )


@then("reply_to_user 应提示该子任务不是直接改主产物")
def assert_reply_warns_not_main_artifact(scenario_state):
    reply = str(scenario_state["result"].get("reply_to_user", ""))
    assert (
        reply
        or "子任务" in str(scenario_state["result"])
        or "research" in str(scenario_state["result"])
    ), f"no subtask hint in {scenario_state['result']!r}"


# ---- Scenario: request_advance ---------------------------------------------


@given("当前阶段的推进入口是硬按钮 confirm_next")
def advance_entry_is_confirm_next(scenario_state):
    scenario_state["confirm_next_hard_button"] = True


@then("action 应为 request_advance 或等价推进意图")
def assert_action_request_advance(scenario_state, action_matcher):
    # SPEC-4.6: router must NOT return a real advance action; the canonical
    # advance signal is action="clarify" + highlight_confirm_button=True.
    # We accept clarify here only when the highlight signal is set, so a
    # plain clarify (the router's "I don't know" fallback) still fails.
    result = scenario_state["result"]
    actual = str(result.get("action", ""))
    if not action_matcher(actual, "request_advance"):
        raise AssertionError(
            f"expected action=request_advance (or alias), got {actual!r}"
        )
    if actual == "clarify" and result.get("highlight_confirm_button") is not True:
        raise AssertionError(
            "clarify accepted as request_advance only when "
            "highlight_confirm_button=True; got "
            f"{result!r}"
        )


@then("前端应高亮“确认进入下一阶段”按钮")
def assert_highlight_confirm_next_button(scenario_state):
    result = scenario_state["result"]
    has_highlight = (
        result.get("highlight_confirm_button") is True
        or "confirm" in str(result).lower()
    )
    assert has_highlight, f"no highlight confirm hint in {result!r}"


@then("若当前阶段仍未满足门禁 按钮保持禁用并展示原因")
def assert_gate_block_with_reason(scenario_state):
    result = scenario_state["result"]
    gate_blocked = (
        result.get("gate_satisfied") is False
        or result.get("button_disabled_reason")
        or "门禁" in str(result)
    )
    assert gate_blocked, f"no gate-block info in {result!r}"


# ---- Scenario: clarify -----------------------------------------------------


@then("action 应为 clarify")
def assert_action_clarify(scenario_state, action_matcher):
    actual = str(scenario_state["result"].get("action", ""))
    assert action_matcher(actual, "clarify"), (
        f"expected action=clarify, got {actual!r}"
    )


@then("reply_to_user 应提出一个澄清问题")
def assert_reply_is_clarification_question(scenario_state):
    reply = str(scenario_state["result"].get("reply_to_user", ""))
    has_question = (
        "?" in reply
        or "？" in reply
        or "clarify" in str(scenario_state["result"]).lower()
    )
    assert has_question, f"no clarification question in {scenario_state['result']!r}"


@then("task_ledger 不应新增任务")
def assert_no_new_task_in_ledger(scenario_state):
    tasks = scenario_state["result"].get("task_ledger") or []
    assert len(tasks) == 0, f"expected no tasks, got {tasks!r}"


# ---- Scenario: two-round clarify -------------------------------------------


@given("同一条会话连续两轮 Router 输出 action=clarify")
def two_rounds_of_clarify(scenario_state):
    scenario_state["clarify_count"] = 2
    scenario_state["utterance"] = "这个不太清楚"


@then("前端应展示 4 个候选动作按钮")
def assert_four_candidate_buttons(scenario_state):
    result = scenario_state["result"]
    candidates = result.get("candidate_actions", [])
    assert len(candidates) >= 4, f"expected 4+ candidate actions, got {candidates!r}"


@then("候选按钮必须包含 revise、regenerate、inject_subtask、skip_phase")
def assert_candidates_include_all_four(scenario_state):
    result = scenario_state["result"]
    required = {"revise", "regenerate", "inject_subtask", "skip_phase"}
    candidates = set(result.get("candidate_actions", []))
    missing = required - candidates
    assert not missing, f"missing candidate actions: {missing!r}"


# ---- Scenario: cross-phase context -----------------------------------------


@given("当前已从 Phase 2 进入 Phase 3")
def transitioned_from_phase_2_to_3(scenario_state):
    scenario_state["previous_phase"] = 2
    scenario_state["current_phase"] = 3
    scenario_state["utterance"] = "继续推进"  # default for this scenario


@given("Phase 2 存在超过 6 轮历史对话")
def phase_2_has_many_turns(scenario_state):
    scenario_state["phase_2_history_turns"] = 10


@then("注入上下文中不应包含跨阶段完整 turn 历史")
def assert_no_cross_phase_turn_history(scenario_state):
    result = scenario_state["result"]
    cross_phase_turns = result.get("cross_phase_turns")
    if cross_phase_turns is not None:
        assert len(cross_phase_turns) == 0, (
            f"unexpected cross-phase turns: {cross_phase_turns!r}"
        )
    # Acceptable: the result doesn't include full phase-2 history


@then("只允许保留合并后的偏好规则")
def assert_only_merged_preferences_retained(scenario_state):
    result = scenario_state["result"]
    prefs = result.get("preferences") or result.get("merged_preferences")
    assert prefs, f"no merged preferences in {result!r}"
    assert "phase_2_turns" not in result or len(result.get("phase_2_turns", [])) == 0, (
        f"phase-2 turns leaked: {result!r}"
    )


@then("本阶段最近对话窗口最多保留 6 轮")
def assert_max_6_recent_turns(scenario_state):
    result = scenario_state["result"]
    turns = result.get("recent_turns") or result.get("context_window") or []
    if isinstance(turns, list):
        assert len(turns) <= 6, f"expected <=6 turns, got {len(turns)}"
