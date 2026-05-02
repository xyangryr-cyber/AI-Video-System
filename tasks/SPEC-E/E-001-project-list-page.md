# [SPEC-E-001] Project List Page

## Metadata
- **task_id**: SPEC-E-001
- **spec_ref**: SPEC-2.1
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: S
- **bdd_tags**: [@navigation]

## Scope
Implement the project list page displaying `title`, `category`, `current_phase`, `progress` (progress bar), `status`, and `updated_at` (relative time). No filtering, search, template, or clone features. `updated_at` must refresh within 6s of a status change via WebSocket subscription.

## Allowed Files
- `src/frontend/pages/ProjectList.tsx`
- `src/frontend/components/ProjectCard.tsx`
- `src/frontend/hooks/useProjects.ts`
- `src/frontend/types/project.ts`
- `tests/unit/frontend/ProjectList.test.tsx`
- `tests/unit/frontend/ProjectCard.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/shared/schemas/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: List page renders `title`, `category`, `current_phase`, `progress`, `status`, `updated_at` for each project
- [ ] AC-2: Progress bar visually reflects `current_phase / 12` (0-100%)
- [ ] AC-3: `updated_at` displays as relative time (e.g. "3 分钟前")
- [ ] AC-4: Creating 3 projects at different phases results in correct progress/status/time display
- [ ] AC-5: `updated_at` refreshes within 6s of a status change event via WebSocket

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_001.py -v
tsc --noEmit
```

## Completion Definition
Project list page renders all required fields, progress bar is visually accurate, relative time updates within 6s of status change. All tests pass, no type errors.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_001.py | test_renders_all_project_fields |
| AC-2 | tests/unit/frontend/test_spec_e_001.py | test_progress_bar_reflects_phase |
| AC-3 | tests/unit/frontend/test_spec_e_001.py | test_updated_at_relative_time |
| AC-4 | tests/unit/frontend/test_spec_e_001.py | test_multiple_projects_different_phases |
| AC-5 | tests/unit/frontend/test_spec_e_001.py | test_updated_at_refreshes_on_ws_event |
