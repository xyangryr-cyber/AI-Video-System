# [SPEC-E-010] CandidateSelector Component

## Metadata
- **task_id**: SPEC-E-010
- **spec_ref**: SPEC-25.1
- **depends_on**: [SPEC-A-001, SPEC-E-003]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement a reusable CandidateSelector component for aesthetic candidate selection, used across P4/P5/P6/P8/P9 phases. State machine: idle -> previewing -> selected -> confirmed. Two-step confirmation flow (select then confirm). Max 3 candidates displayed. 60s inactivity timeout triggers a one-time reminder toast ("已等待 60 秒，请选择一个候选方案，或点击「跳过并接受推荐」"; no repeat; no auto-select). "Skip and accept recommendation" button confirms the `is_recommended=true` candidate. Confirmed selection calls `POST /api/projects/{id}/preferences/confirm` with the chosen candidate_id.

## Allowed Files
- `src/frontend/components/CandidateSelector.tsx`
- `src/frontend/components/CandidateCard.tsx`
- `src/frontend/hooks/useCandidateSelection.ts`
- `src/frontend/types/candidates.ts`
- `tests/unit/frontend/CandidateSelector.test.tsx`
- `tests/unit/frontend/useCandidateSelection.test.ts`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Component displays up to 3 candidates with preview capability
- [ ] AC-2: State machine transitions: idle -> previewing (on hover/click) -> selected (on select) -> confirmed (on confirm)
- [ ] AC-3: Two-step confirmation: user must select then explicitly confirm (not single-click confirm)
- [ ] AC-4: After 60s of no interaction, displays reminder toast with exact wording from spec; reminder fires only once; no auto-selection
- [ ] AC-5: "Skip and accept recommendation" button confirms the candidate with `is_recommended=true`
- [ ] AC-6: Confirmation calls `POST /api/projects/{id}/preferences/confirm` with `candidate_id` in decisions payload
- [ ] AC-7: Component is reusable across P4, P5, P6, P8, P9 phases (accepts generic Candidate interface)
- [ ] AC-8: style_lock unlock requires explicit action (navigating back to P7); no unlock button in CandidateSelector

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_010.py -v
tsc --noEmit
```

## Completion Definition
CandidateSelector component implements full state machine, two-step confirmation, 60s timeout reminder (once only), skip-to-recommended flow, and calls correct API. Reusable across 5 phases. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_010.py | test_displays_up_to_3_candidates |
| AC-2 | tests/unit/frontend/test_spec_e_010.py | test_state_machine_transitions |
| AC-3 | tests/unit/frontend/test_spec_e_010.py | test_two_step_confirmation |
| AC-4 | tests/unit/frontend/test_spec_e_010.py | test_60s_timeout_reminder_once |
| AC-5 | tests/unit/frontend/test_spec_e_010.py | test_skip_accepts_recommended |
| AC-6 | tests/unit/frontend/test_spec_e_010.py | test_confirm_calls_preferences_api |
| AC-7 | tests/unit/frontend/test_spec_e_010.py | test_reusable_across_phases |
| AC-8 | tests/unit/frontend/test_spec_e_010.py | test_no_unlock_button |
