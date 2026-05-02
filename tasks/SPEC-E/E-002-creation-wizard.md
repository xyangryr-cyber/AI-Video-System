# [SPEC-E-002] Project Creation Wizard

## Metadata
- **task_id**: SPEC-E-002
- **spec_ref**: SPEC-2.2
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: S

## Scope
Implement a two-field project creation form (title + natural language description with >= 10 character validation). On successful submission, call `POST /api/projects` and redirect to the workflow page with phase navigation highlighting P0.

## Allowed Files
- `src/frontend/pages/CreateProject.tsx`
- `src/frontend/components/CreateProjectForm.tsx`
- `src/frontend/hooks/useCreateProject.ts`
- `tests/unit/frontend/CreateProjectForm.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Form displays two fields: title (required) and description (required, >= 10 chars)
- [ ] AC-2: Description < 10 chars triggers client-side validation error, form does not submit
- [ ] AC-3: Successful submission calls `POST /api/projects` with title + description
- [ ] AC-4: After successful creation, browser navigates to workflow page (`/projects/{id}`)
- [ ] AC-5: Workflow page phase navigation highlights P0 on arrival

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_002.py -v
tsc --noEmit
```

## Completion Definition
Creation wizard validates input client-side, calls correct API endpoint, and redirects to workflow page with P0 highlighted. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_002.py | test_renders_title_and_description_fields |
| AC-2 | tests/unit/frontend/test_spec_e_002.py | test_rejects_short_description |
| AC-3 | tests/unit/frontend/test_spec_e_002.py | test_submits_to_create_api |
| AC-4 | tests/unit/frontend/test_spec_e_002.py | test_redirects_to_workflow_page |
| AC-5 | tests/unit/frontend/test_spec_e_002.py | test_phase_nav_highlights_p0 |
