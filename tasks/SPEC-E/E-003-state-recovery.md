# [SPEC-E-003] State Recovery on Page Load

## Metadata
- **task_id**: SPEC-E-003
- **spec_ref**: SPEC-2.3
- **depends_on**: [SPEC-A-001, SPEC-E-001]
- **priority**: P0
- **estimated_complexity**: M
- **bdd_tags**: [@navigation]

## Scope
On workflow page load (or browser refresh / device switch), call `GET /projects/{id}/state` and render the full `ProjectState` response. Ensure all fields are non-undefined, phase navigation reflects `current_phase`, preview area renders correct phase component, and progress resumes within 10s. Handle loading and error states.

## Allowed Files
- `src/frontend/pages/WorkflowPage.tsx`
- `src/frontend/hooks/useProjectState.ts`
- `src/frontend/components/PhaseNavigation.tsx`
- `src/frontend/components/LoadingState.tsx`
- `src/frontend/components/ErrorState.tsx`
- `tests/unit/frontend/WorkflowPage.test.tsx`
- `tests/unit/frontend/useProjectState.test.ts`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Page load calls `GET /projects/{id}/state` and renders all ProjectState fields
- [ ] AC-2: No field in the rendered state is `undefined` (verified against ProjectState interface)
- [ ] AC-3: Phase navigation highlights `current_phase` from restored state
- [ ] AC-4: Preview area renders the correct phase-specific component based on `current_phase`
- [ ] AC-5: State recovery completes within 10s (loading indicator shown during fetch)
- [ ] AC-6: API failure renders error state with retry button

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_003.py -v
tsc --noEmit
```

## Completion Definition
Workflow page fully restores project state from API on load, renders correct phase, shows loading/error states. All fields populated, no undefined values. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_003.py | test_fetches_project_state_on_mount |
| AC-2 | tests/unit/frontend/test_spec_e_003.py | test_no_undefined_fields_in_state |
| AC-3 | tests/unit/frontend/test_spec_e_003.py | test_phase_nav_highlights_current_phase |
| AC-4 | tests/unit/frontend/test_spec_e_003.py | test_renders_correct_phase_component |
| AC-5 | tests/unit/frontend/test_spec_e_003.py | test_shows_loading_during_fetch |
| AC-6 | tests/unit/frontend/test_spec_e_003.py | test_error_state_with_retry |
