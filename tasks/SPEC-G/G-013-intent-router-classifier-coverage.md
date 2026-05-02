# [SPEC-G-013] IntentRouter classifier 关键词覆盖 + cross-phase 测试入口对齐

## Metadata
- **task_id**: SPEC-G-013
- **spec_ref**: SPEC-C-006 (SPEC-4.1, 4.2, 4.4, 4.6) — `docs/specs/SPEC-C-backend-core.md` lines 122-181
- **depends_on**: [SPEC-G-012]  (parsers ambiguity fixed in 1179fe9; ACTION_ALIASES matcher in 55296f8)
- **priority**: P0  (G-012 task card completion blocker; product-core conversation classifier coverage)
- **estimated_complexity**: M
- **TDD 起点**: 4 router BDD scenarios currently FAIL with action=clarify because `IntentRouter.classify()` is a stub that only handles revise. Treat 3 of those 4 as RED (regenerate / request_advance / cross-phase). The 4th (inject_subtask) is DEFERRED to G-014 — see "Out of Scope" below.

## Background

`tests/eval/bdd/test_classification_bdd.py` currently passes 3/7 router scenarios after G-012's deepeval removal (commits 55296f8 + 1179fe9). The remaining 4 failures break down as:

| Scenario | Failure root cause | Fixable in G-013? |
|---|---|---|
| 用户要求整体重做时识别为 regenerate | `classify()` stub doesn't detect "整体重做" / "重新生成" keywords | **Yes — keyword rule** |
| 用户要求补充调研时识别为 inject_subtask | No canonical `inject_subtask` / research action in `AVAILABLE_ACTIONS` (SPEC-4.6 enum) | **No — defer to G-014 (requires SPEC-C extension)** |
| 用户表达下一步意图时不直接推进而是引导 confirm_next | `classify()` stub doesn't detect "下一步" keyword AND has no `highlight_confirm_button` signal | **Yes — keyword rule + extra return field** |
| 跨阶段不继承无关对话历史 | Scenario asserts `result.preferences` / `result.recent_turns`, but `classify()` returns `{action, params, task_ledger}` only. SPEC-4.2 conversation-window + preferences logic actually lives in `IntentRouter.build_context()`, not `classify()` | **Yes — rewire BDD `When` step to call `build_context()`** |

**Why classify() is the right entry for keyword rules** (not `route()`): `route()` runs the LLM call path with timeout + JSON parse fallback (SPEC-4.4). `classify()` is the rule-based deterministic shortcut used by BDD evaluation scenarios; keeping it stateless + zero-cost is intentional.

## Scope

### In scope (G-013)
1. Extend `IntentRouter.classify()` with keyword rules for:
   - **regenerate intent** → return `action="regenerate_section"` (canonical `AVAILABLE_ACTIONS` member; matches `ACTION_ALIASES["regenerate"]` set in `tests/eval/bdd/conftest.py`)
   - **advance intent** → return `action="clarify"` with `highlight_confirm_button=True` and a `reply_to_user` hint pointing the user to the hard button (per SPEC-4.6: Router MUST NOT return executable advance action; this is a UI signal only)
2. Rewire cross-phase BDD `When` step to call `IntentRouter.build_context()` instead of `classify()`. Provide synthetic `conversation_history` simulating "post phase-2-to-3 transition with merged prefs" and assert SPEC-4.2 invariants (last-6 window, preferences carried, no full phase-2 turn list).
3. Update `ACTION_ALIASES` in `tests/eval/bdd/conftest.py` if needed to keep matcher contract in sync (e.g., `"request_advance"` should accept `"clarify"` only when accompanied by `highlight_confirm_button=True` — see Implementation Notes).

### Out of scope (defer to G-014)
- **inject_subtask / research action** — `AVAILABLE_ACTIONS` does not include a canonical name for "spawn research subtask"; closest is `insert_section` but semantics differ (insert section content vs. spawn subtask). Adding a new action requires SPEC-C-backend-core.md edit, which is in `forbidden_files` (HARNESS §1.2). G-014 should: (a) propose canonical action name + return shape to SPEC owner, (b) implement classifier rule once SPEC accepts.

## Allowed Files
- `src/backend/agents/intent_router.py`  (extend `classify()` only; do NOT change `AVAILABLE_ACTIONS`, `route()`, `build_context()` signatures)
- `tests/eval/bdd/steps/classification_steps.py`  (rewire cross-phase `When` step + adjust `assert_action_request_advance` to also check `highlight_confirm_button` if needed)
- `tests/eval/bdd/conftest.py`  (extend `ACTION_ALIASES` only if matcher contract needs to expand; document rationale in code comment)
- `tests/unit/backend-core/test_intent_router_classify.py`  (NEW file — TDD RED tests for the new keyword rules; place next to existing intent_router tests)

## Forbidden Files
- `docs/specs/**`  (SPEC is read-only)
- `tests/eval/bdd/features/router.feature`  (auto-generated — fix in source `.feature.md` if scenario text needs change)
- `src/backend/agents/intent_router.py::AVAILABLE_ACTIONS`  (do NOT add new members; that's G-014 + SPEC change)
- `src/backend/agents/intent_router.py::route()`  (LLM path, SPEC-4.4 contract — out of scope)
- `src/backend/agents/intent_router.py::build_context()`  (SPEC-4.2 contract — already correct, do not modify; only the BDD test harness should change to point at it)

## Implementation Notes

### 1. Keyword rules for `classify()`

Add detection patterns at the top of `classify()`, before the existing revise regex. Rule order matters: more specific patterns first.

**Regenerate intent** (return `regenerate_section`):
- Trigger keywords (any one): `整体重做`, `推倒重来`, `重做`, `重新生成`, `regenerate`, `重新写`
- Return shape:
  ```python
  return {
      "action": "regenerate_section",
      "params": {"scope": "full"},
      "task_ledger": [{"type": "generate_artifact", "scope": "full"}],
  }
  ```
- Matches BDD assertions in `assert_action_matches` (via `ACTION_ALIASES["regenerate"]`), `assert_params_scope_full`, `assert_generate_or_regenerate_task`.

**Advance intent** (return `clarify` + highlight signal):
- Trigger keywords (any one, requires word boundary to avoid false positives): `下一步`, `进入下一阶段`, `推进`, `继续推进`, `next phase`
- Return shape:
  ```python
  return {
      "action": "clarify",
      "params": {},
      "task_ledger": [],
      "highlight_confirm_button": True,
      "gate_satisfied": False,  # router does not know gate state; defaults to False so gate-block hint fires
      "button_disabled_reason": "等待门禁条件满足",
      "reply_to_user": "请点击「确认进入下一阶段」按钮推进",
  }
  ```
- Matches BDD assertions: `assert_highlight_confirm_next_button` (checks `highlight_confirm_button is True`), `assert_gate_block_with_reason` (checks `gate_satisfied is False` or `button_disabled_reason` set).

**ACTION_ALIASES update** (in `tests/eval/bdd/conftest.py`):
- The current alias `"request_advance" → {"request_advance", "confirm_next", "advance"}` won't match `clarify`. Two acceptable resolutions:
  - **Option A (recommended)**: Add `"clarify"` to the `"request_advance"` alias set, gated semantically by the BDD step. Update `assert_action_request_advance` to ALSO check `result.get("highlight_confirm_button") is True` so plain clarify (non-advance) still fails the assertion.
  - **Option B**: Add a parallel matcher fixture for "advance-clarify" combo; more code, less centralized.
- Choose A. Document in conftest.py why `clarify` is conditionally accepted as `request_advance` (because SPEC-4.6 forbids a real advance action).

### 2. Cross-phase BDD rewire

Current `When` step in `classification_steps.py`:
```python
@when("IntentRouter 在 Phase 3 第一次被调用")
def router_called_in_phase_3(scenario_state):
    scenario_state["phase"] = 3
    _router_classify(scenario_state)
```

This calls `classify()` which doesn't expose SPEC-4.2 context invariants. Rewrite to:
```python
@when("IntentRouter 在 Phase 3 第一次被调用")
def router_called_in_phase_3(scenario_state):
    from src.backend.agents.intent_router import IntentRouter

    # Simulate post-transition state: caller (PhaseTransitionService, future) is
    # expected to filter conversation_history to current phase + pass merged prefs.
    # build_context applies the SPEC-4.2 6-turn window on top of that.
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
```

The Then assertions already check `result.preferences` and `result.recent_turns` shapes; this rewire makes them point at the right fixture data.

### 3. TDD plan (RED first)

Create `tests/unit/backend-core/test_intent_router_classify.py` with RED tests BEFORE implementing rules:

```python
def test_classify_recognizes_regenerate_intent():
    result = IntentRouter().classify("这版大纲不对，整体重做")
    assert result["action"] == "regenerate_section"
    assert result["params"]["scope"] == "full"
    assert any(t["type"] == "generate_artifact" for t in result["task_ledger"])

def test_classify_recognizes_advance_intent_returns_clarify_with_hint():
    result = IntentRouter().classify("好了，下一步")
    assert result["action"] == "clarify"  # SPEC-4.6: no real advance action
    assert result["highlight_confirm_button"] is True
    assert result["gate_satisfied"] is False
    assert "确认" in result["reply_to_user"]

def test_classify_falls_back_to_clarify_for_unknown():
    result = IntentRouter().classify("嗯……感觉怪怪的")
    assert result["action"] == "clarify"
    assert result.get("highlight_confirm_button") is not True

def test_classify_revise_unchanged_by_new_rules():
    # Regression guard: existing revise rule must still win for "第N段+改"
    result = IntentRouter().classify("把第二段改得更口语化")
    assert result["action"] == "revise"
```

Run RED first to confirm all 4 fail for the right reason, THEN implement keyword rules to make them pass.

## Acceptance Criteria

- [ ] AC-1: `pytest tests/unit/backend-core/test_intent_router_classify.py -v` → 4 passed (the 4 new RED→GREEN tests)
- [ ] AC-2: `pytest tests/unit/backend-core/test_intent_router*.py -q` → no regression vs. baseline (existing classify revise + route + build_context tests stay green)
- [ ] AC-3: `AVS_EVAL_MODE=1 pytest tests/eval/bdd/test_classification_bdd.py -v` → **6 passed, 1 failed** where the 1 fail is `test_用户要求补充调研时识别为_inject_subtask` (deferred to G-014)
- [ ] AC-4: `assert_action_request_advance` step now checks BOTH `action_matcher(actual, "request_advance")` AND `result.get("highlight_confirm_button") is True` — so plain `clarify` (without advance hint) still fails this assertion
- [ ] AC-5: `IntentRouter.AVAILABLE_ACTIONS` tuple unchanged (zero diff in this constant — verified via grep)
- [ ] AC-6: `route()` and `build_context()` method signatures unchanged
- [ ] AC-7: `ruff check` + `mypy --explicit-package-bases` clean for all touched files
- [ ] AC-8: `python3 scripts/contracts/verify_no_skip_stubs.py` → GATE PASSED (no new stubs introduced)

## Verification Commands

```bash
# RED phase verification
.venv/bin/python3 -m pytest tests/unit/backend-core/test_intent_router_classify.py -v
# expect: 4 failed (for the right reason — assertion on missing keys)

# GREEN phase verification
.venv/bin/python3 -m pytest tests/unit/backend-core/test_intent_router_classify.py -v
# expect: 4 passed

# Regression
.venv/bin/python3 -m pytest tests/unit/backend-core/ -q
# expect: no regression vs. baseline (currently 2068 passed, 1 skipped per PROGRESS.md)

# BDD acceptance
AVS_EVAL_MODE=1 .venv/bin/python3 -m pytest tests/eval/bdd/test_classification_bdd.py -v
# expect: 6 passed, 1 failed (the failed one MUST be inject_subtask — any other failure is a regression)

# Lint + type
.venv/bin/python3 -m ruff check src/backend/agents/intent_router.py tests/eval/bdd/conftest.py tests/eval/bdd/steps/classification_steps.py tests/unit/backend-core/test_intent_router_classify.py
.venv/bin/python3 -m mypy src/backend/agents/intent_router.py tests/eval/bdd/conftest.py tests/eval/bdd/steps/classification_steps.py --explicit-package-bases

# Stub gate
.venv/bin/python3 scripts/contracts/verify_no_skip_stubs.py

# Invariant guard (manual)
grep -n "AVAILABLE_ACTIONS" src/backend/agents/intent_router.py
# expect: tuple unchanged from current version
```

## Completion Definition

`AVS_EVAL_MODE=1 pytest tests/eval/bdd/test_classification_bdd.py -v` returns 6 passed, 1 failed, where the only fail is `test_用户要求补充调研时识别为_inject_subtask` (deferred to G-014 with documented SPEC-extension dependency). All 8 ACs check. After GREEN, append commit row `| <sha> | SPEC-G-013 | ... | <date> |` to PROGRESS.md and update the G-012 Open follow-up bullet to link to G-014 for the remaining inject_subtask gap.

## Test Mapping

| AC | Test Type | Test File | Test Function / Scenario |
|---|---|---|---|
| AC-1 | unit | `tests/unit/backend-core/test_intent_router_classify.py` | 4 new tests (regenerate / advance-clarify / unknown-clarify / revise-regression) |
| AC-2 | unit | `tests/unit/backend-core/test_intent_router*.py` | full suite |
| AC-3 | BDD eval | `tests/eval/bdd/test_classification_bdd.py` | 7 router scenarios — assert exactly inject_subtask fails |
| AC-4 | BDD eval | `tests/eval/bdd/test_classification_bdd.py::test_用户表达下一步意图时不直接推进而是引导_confirm_next` | passes only when classify returns clarify+highlight |
| AC-5 | invariant | `src/backend/agents/intent_router.py` | grep AVAILABLE_ACTIONS unchanged |
| AC-6 | invariant | `src/backend/agents/intent_router.py` | grep `def route(` and `def build_context(` signatures unchanged |
| AC-7 | static | n/a | ruff + mypy clean |
| AC-8 | contract | n/a | `verify_no_skip_stubs.py` GATE PASSED |

## Rollback Path

Pure additive change in `classify()`. Rollback = `git revert <sha>` of the GREEN commit; nothing else depends on the new keyword rules.

## Risk Notes

1. **Keyword over-matching**: "重做" appears in benign sentences ("我得重做笔记")。Mitigate by requiring the keyword to appear in a directive context (sentence-final or with imperative markers like "把"/"请"). Or accept some false positives — the user can always say "no" via the next turn.
2. **Action enum drift**: If SPEC-C ever renames `regenerate_section` (e.g., to `regenerate`), the `ACTION_ALIASES["regenerate"]` set would need an update. Add a unit test pinning the alias to current AVAILABLE_ACTIONS member.
3. **highlight_confirm_button leakage**: This field is only meaningful when `action == "clarify"` AND advance intent was detected. Frontend must not key off `highlight_confirm_button` for non-clarify actions. Document in the IntentRouter docstring.

## Handoff Checklist (for executing AI)

- [ ] Read SPEC-C §SPEC-4.1, §SPEC-4.2, §SPEC-4.4, §SPEC-4.6 (lines 122-181 of `docs/specs/SPEC-C-backend-core.md`) before touching code
- [ ] Run RED tests first (AC-1 expect 4 failed)
- [ ] Implement keyword rules in `classify()`
- [ ] Run RED tests again (expect 4 passed = GREEN)
- [ ] Update conftest.py ACTION_ALIASES if needed (per Implementation Notes 1, Option A)
- [ ] Update `assert_action_request_advance` to also check `highlight_confirm_button` (AC-4)
- [ ] Rewire cross-phase `When` step (per Implementation Notes 2)
- [ ] Run BDD eval (AC-3) — expect exactly inject_subtask fails
- [ ] Run regression (AC-2)
- [ ] Run lint/type/stub-gate
- [ ] Commit per HARNESS §9.3 with `[SPEC-G-013]` prefix; body includes Files Changed / Verification (real outputs) / Decisions / Artifacts
- [ ] Update PROGRESS.md (one row + close G-012 follow-up referencing G-014 for inject_subtask)
- [ ] If you discover any blocker not in Risk Notes above, STOP and document the blocker — do not extend AVAILABLE_ACTIONS or change SPEC files
