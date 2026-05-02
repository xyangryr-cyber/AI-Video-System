# [SPEC-A-105] Frontend Type ↔ Backend Schema Contract Consistency Test

## Metadata
- **task_id**: SPEC-A-105
- **spec_ref**: docs/superpowers/specs/2026-04-17-frontend-prototype-integration-design.md §4.3; HARNESS §5.1
- **depends_on**: [SPEC-A-001, SPEC-A-002, SPEC-A-004]
- **priority**: P0
- **estimated_complexity**: M

## Scope
A pytest-based test that emits JSON Schema from every Pydantic model in `src/shared/schemas/`, parses every interface from `src/frontend/types/*.ts` (and `src/shared/types/*.ts`), and asserts field-level parity (name, optionality, primitive types, enum values). Runs in CI and blocks PRs on drift.

## Allowed Files
- `tests/contract/__init__.py`
- `tests/contract/test_frontend_types_match_schemas.py`
- `scripts/extract_ts_types.py`
- `scripts/emit_json_schemas.py` (shared with SPEC-B-017; idempotent if already created)
- `tests/unit/infra/test_extract_ts_types.py`

## Forbidden Files
- `src/frontend/types/**` (read-only)
- `src/shared/schemas/**` (read-only)
- `src/shared/types/**` (read-only)

## Acceptance Criteria
- [ ] AC-1: `scripts/emit_json_schemas.py` emits one JSON Schema per Pydantic model in `src/shared/schemas/` to `build/schemas/*.json`.
- [ ] AC-2: `scripts/extract_ts_types.py` parses TypeScript interfaces/type aliases and yields `{name, fields:[{name, type, optional}]}` records.
- [ ] AC-3: `pytest tests/contract/test_frontend_types_match_schemas.py` passes when types align with current schemas.
- [ ] AC-4: Removing a field from any TS interface causes the test to fail with a precise message naming the interface, schema, and missing field.
- [ ] AC-5: Adding an extra field to any TS interface (not in the schema) causes the test to fail.
- [ ] AC-6: Test runs in PR CI (added by Task 12).

## Verification Commands
```bash
python scripts/emit_json_schemas.py
python scripts/extract_ts_types.py src/shared/types src/frontend/types
pytest tests/contract/test_frontend_types_match_schemas.py -v
pytest tests/unit/infra/test_extract_ts_types.py -v
```

## Completion Definition
Schema drift between frontend TS types and backend Pydantic models is caught at PR time with actionable error messages.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-3 | tests/contract/test_frontend_types_match_schemas.py | `test_all_shared_types_match_schemas` |
| AC-4 | tests/contract/test_frontend_types_match_schemas.py | `test_missing_field_in_ts_fails` |
| AC-5 | tests/contract/test_frontend_types_match_schemas.py | `test_extra_field_in_ts_fails` |
| AC-2 | tests/unit/infra/test_extract_ts_types.py | `test_parses_simple_interface`, `test_marks_optional_fields` |
