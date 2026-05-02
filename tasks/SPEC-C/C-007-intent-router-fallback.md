# [SPEC-C-007] IntentRouter Error Handling, Clarify Flow & confirm_next Bypass

## Metadata
- **task_id**: SPEC-C-007
- **spec_ref**: SPEC-4.4, SPEC-4.5, SPEC-4.6
- **depends_on**: [SPEC-C-006]
- **priority**: P1
- **estimated_complexity**: S

## Scope
Implement Router fallback behavior: 3-second timeout and JSON parse failure both degrade to `clarify` action (not 500). Log all fallbacks with `router_fallback` event. After 2 consecutive clarify responses, return candidate action buttons (<=4) for frontend display. Counter resets on successful operation. `confirm_next` is a hard button routed directly to the API, never through the Router.

## Allowed Files
- `src/backend/agents/intent_router.py`
- `tests/unit/backend-core/test_intent_router_fallback.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: LLM returning non-JSON causes Router to return `clarify` action, not HTTP 500
- [ ] AC-2: LLM exceeding 3s timeout causes Router to return `clarify` action
- [ ] AC-3: All fallback scenarios produce a `router_fallback` log entry
- [ ] AC-4: After 2 consecutive clarify responses, output includes <=4 candidate action buttons
- [ ] AC-5: Successful operation resets clarify counter to 0
- [ ] AC-6: User typing "push to next phase" does NOT cause Router to return an advance action

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_007.py -v
ruff check src/backend/agents/intent_router.py
```

## Completion Definition
Router gracefully degrades on timeout/parse errors, logs fallbacks, triggers button suggestions after 2 clarifies, and never routes confirm_next. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_007.py | test_non_json_returns_clarify |
| AC-2 | tests/unit/backend-core/test_spec_c_007.py | test_timeout_returns_clarify |
| AC-3 | tests/unit/backend-core/test_spec_c_007.py | test_fallback_logs_event |
| AC-4 | tests/unit/backend-core/test_spec_c_007.py | test_two_clarifies_show_buttons |
| AC-5 | tests/unit/backend-core/test_spec_c_007.py | test_success_resets_clarify_count |
| AC-6 | tests/unit/backend-core/test_spec_c_007.py | test_advance_text_not_routed |
