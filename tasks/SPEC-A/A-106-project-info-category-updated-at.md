# [SPEC-A-106] ProjectInfo + category + updated_at (v3.18 D1)

## Metadata
- **task_id**: SPEC-A-106
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D1
- **depends_on**: [SPEC-A-002, SPEC-A-105]
- **priority**: P0
- **estimated_complexity**: S

## Scope
Add `category: str` and `updated_at: str` (ISO 8601) to `ProjectInfo`. Update TS mirror, fixtures, and `_index.json`. `category` captures business classification (E-001 AC-1). `updated_at` is the raw ISO timestamp; frontend formats it as relative time.

## Allowed Files
- src/shared/schemas/project_state.py
- src/shared/types/project_state.ts
- tests/fixtures/api/projects/list_response.json
- tests/fixtures/api/projects/detail_p3.json
- tests/fixtures/api/projects/_index.json
- tests/unit/contracts/test_spec_a_106.py

## Forbidden Files
- All files outside the Allowed Files list

## Acceptance Criteria
- [ ] AC-1: `ProjectInfo` Pydantic model has fields `category: str` (min_length=1) and `updated_at: str` (min_length=1).
- [ ] AC-2: TS `ProjectInfo` interface has matching `category: string` and `updated_at: string` fields.
- [ ] AC-3: Both fixtures include both new fields with realistic ISO 8601 timestamps and Chinese category labels.
- [ ] AC-4: `pytest tests/contract/test_frontend_types_match_schemas.py` passes.
- [ ] AC-5: `python scripts/validate_fixtures.py` passes.

## Verification Commands
```bash
/opt/homebrew/bin/python3.13 -m pytest tests/unit/contracts/test_spec_a_106.py -v
/opt/homebrew/bin/python3.13 -m pytest tests/contract/test_frontend_types_match_schemas.py -v
/opt/homebrew/bin/python3.13 scripts/validate_fixtures.py
```

## Completion Definition
ProjectInfo carries category + updated_at end-to-end (Pydantic, TS, fixture, contract test green).
