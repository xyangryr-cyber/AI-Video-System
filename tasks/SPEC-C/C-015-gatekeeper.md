# [SPEC-C-015] GateKeeper (7-Item Gate Check + Skip Branch + Claude Model)

## Metadata
- **task_id**: SPEC-C-015
- **spec_ref**: SPEC-8.1, SPEC-8.2, SPEC-8.3, SPEC-8.4
- **depends_on**: [SPEC-A-001, SPEC-C-002, SPEC-C-005, SPEC-C-010, SPEC-C-011]
- **priority**: P0
- **estimated_complexity**: L
- **bdd_tags**: [@observability, @gatekeeper]

## Scope
Implement GateKeeper with 7 check items for advance: (1) artifact exists, (2) version matches latest review, (3) review verdict=PASS, (4) no in-progress task_ledger tasks, (5) no running async_tasks, (6) preferences confirmed, (7) cost recorded (non-blocking WARN). Gate failure returns ALL failed items (no short-circuit). Skip branch only checks items 4 and 6. Reviewer verdict is strictly PASS/FAIL binary; blocking_issues=[] implies PASS. GateKeeper LLM calls use Claude (from model_config.json `gatekeeper` key).

## Allowed Files
- `src/backend/engine/gatekeeper.py`
- `src/backend/engine/__init__.py`
- `tests/unit/backend-core/test_gatekeeper.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/shared/schemas/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Each of the 7 check items fails independently with a specific failure reason
- [ ] AC-2: All 7 items passing results in advance success
- [ ] AC-3: Gate failure returns ALL failed items, not just the first (no short-circuit)
- [ ] AC-4: Skip mode only checks "no in-progress tasks" (#4) and "preferences confirmed" (#6)
- [ ] AC-5: Skip does not block on missing artifact or failed review
- [ ] AC-6: Skip with in-progress tasks still blocks
- [ ] AC-7: Reviewer verdict is strictly PASS or FAIL; blocking_issues=[] forces PASS
- [ ] AC-8: GateKeeper model from `model_config.json` gatekeeper key is a Claude model
- [ ] AC-9: Actual LLM call log shows model matching config
- [ ] AC-10: Cost check (#7) missing does not block advance (WARN only)

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_015.py -v
ruff check src/backend/engine/gatekeeper.py
mypy src/backend/engine/gatekeeper.py --strict
```

## Completion Definition
GateKeeper checks all 7 items, returns comprehensive failure details, supports skip branch, enforces binary verdict, uses Claude model. Cost check is non-blocking. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_015.py | test_each_check_fails_independently |
| AC-2 | tests/unit/backend-core/test_spec_c_015.py | test_all_pass_advance_succeeds |
| AC-3 | tests/unit/backend-core/test_spec_c_015.py | test_no_short_circuit_all_failures |
| AC-4 | tests/unit/backend-core/test_spec_c_015.py | test_skip_checks_only_4_and_6 |
| AC-5 | tests/unit/backend-core/test_spec_c_015.py | test_skip_no_artifact_ok |
| AC-6 | tests/unit/backend-core/test_spec_c_015.py | test_skip_in_progress_blocks |
| AC-7 | tests/unit/backend-core/test_spec_c_015.py | test_verdict_binary_pass_fail |
| AC-8 | tests/unit/backend-core/test_spec_c_015.py | test_gatekeeper_uses_claude_model |
| AC-9 | tests/unit/backend-core/test_spec_c_015.py | test_call_log_matches_config |
| AC-10 | tests/unit/backend-core/test_spec_c_015.py | test_cost_check_non_blocking |
