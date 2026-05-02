# [SPEC-E-009] Error State UX (3-Tier Classification + ERROR_UX_MAP)

## Metadata
- **task_id**: SPEC-E-009
- **spec_ref**: SPEC-24.1
- **depends_on**: [SPEC-A-001, SPEC-E-003]
- **priority**: P1
- **estimated_complexity**: M
- **bdd_tags**: [@error_ux]

## Scope
Implement the 3-tier error UX system and the programmatic ERROR_UX_MAP that maps error codes to UI treatment. Tier 1 (auto_handling): non-blocking toast with ETA, auto-retry up to 3 times. Tier 2 (user_choice): modal with >= 2 action buttons. Tier 3 (user_action): modal with expandable technical details. The ERROR_UX_MAP is a static lookup table (no LLM calls) covering all 8 error codes from SPEC-A SPEC-13A. Components: ErrorToast, ErrorModal, ErrorUxMapper utility.

## Allowed Files
- `src/frontend/components/errors/ErrorToast.tsx`
- `src/frontend/components/errors/ErrorModal.tsx`
- `src/frontend/components/errors/TechnicalDetails.tsx`
- `src/frontend/utils/errorUxMap.ts`
- `src/frontend/hooks/useErrorHandler.ts`
- `src/frontend/types/errors.ts`
- `tests/unit/frontend/errors/ErrorToast.test.tsx`
- `tests/unit/frontend/errors/ErrorModal.test.tsx`
- `tests/unit/frontend/errors/errorUxMap.test.ts`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: ERROR_UX_MAP maps all 8 error codes (EVID_3002, EVID_3004, EVID_4001, EVID_4002, EVID_2001, EVID_5001, EVID_5002, EVID_3001) to tier + component + recovery actions
- [ ] AC-2: ERROR_UX_MAP contains zero LLM calls -- pure static lookup
- [ ] AC-3: auto_handling errors (EVID_3002, EVID_3004) render non-blocking toast with ETA, do not obscure main UI
- [ ] AC-4: user_choice errors (EVID_4001, EVID_4002, EVID_2001) render modal with >= 2 action buttons
- [ ] AC-5: user_action errors (EVID_5001, EVID_5002, EVID_3001) render modal with expandable technical details section
- [ ] AC-6: Each error code in the map has at least one associated recovery action
- [ ] AC-7: Unknown error codes fall back to user_action tier with generic modal

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_009.py -v
tsc --noEmit
```

## Completion Definition
ERROR_UX_MAP covers all 8 error codes with correct tier assignment. Toast and modal components render correctly per tier. No LLM dependency. Unknown codes handled gracefully. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_009.py | test_maps_all_8_error_codes |
| AC-2 | tests/unit/frontend/test_spec_e_009.py | test_no_llm_calls_in_map |
| AC-3 | tests/unit/frontend/test_spec_e_009.py | test_auto_handling_toast_non_blocking |
| AC-4 | tests/unit/frontend/test_spec_e_009.py | test_user_choice_modal_with_buttons |
| AC-5 | tests/unit/frontend/test_spec_e_009.py | test_user_action_modal_expandable_details |
| AC-6 | tests/unit/frontend/test_spec_e_009.py | test_each_code_has_recovery_action |
| AC-7 | tests/unit/frontend/test_spec_e_009.py | test_unknown_code_fallback |
