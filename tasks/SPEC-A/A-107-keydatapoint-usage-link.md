# [SPEC-A-107] KeyDataPoint + usage + link (v3.18 D5)

## Metadata
- **task_id**: SPEC-A-107
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D5
- **depends_on**: [SPEC-A-105]
- **priority**: P1
- **estimated_complexity**: S

## Scope
Add `usage: Optional[str]` and `link: Optional[str]` to `KeyDataPoint`. `usage` is a cross-reference string (e.g., "S2E1 / P4 / P6") that records where this data point was consumed. `link` is the primary-source URL. Adopted from prototype Veritas modal (D5).

## Allowed Files
- src/shared/schemas/shared_types.py
- src/shared/types/shared_types.ts
- tests/fixtures/api/projects/key_data_points.json
- tests/fixtures/api/projects/_index.json
- tests/unit/contracts/test_spec_a_107.py
- scripts/validate_fixtures.py (if list:true support is missing)

## Acceptance Criteria
- [ ] AC-1: KeyDataPoint Pydantic model accepts both fields as Optional.
- [ ] AC-2: TS interface mirrors with `usage?: string` and `link?: string`.
- [ ] AC-3: Fixture demonstrates a populated entry; another with both omitted.
- [ ] AC-4: Contract test passes; fixture validator passes.

## Verification Commands
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_107.py -v
```

## Test Mapping
| AC | Test Function | File |
|----|--------------|------|
| AC-1 | test_keydatapoint_accepts_usage_and_link | tests/unit/contracts/test_spec_a_107.py |
| AC-1 | test_keydatapoint_omits_usage_and_link_when_not_provided | tests/unit/contracts/test_spec_a_107.py |
