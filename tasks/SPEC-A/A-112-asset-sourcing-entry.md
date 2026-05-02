# [SPEC-A-112] AssetSourcingEntry (v3.18 D10)

## Metadata
- **task_id**: SPEC-A-112
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D10
- **depends_on**: [SPEC-A-105]

## Scope
Per-storyboard-shot asset sourcing state from P8 agent: status enum + need/action/data details.

## Acceptance Criteria
- [ ] AC-1: AssetSourcingEntry has shot_id, status, need (Optional), action (Optional), data (Optional dict).
- [ ] AC-2: status is Literal["not_needed","fetched"].
- [ ] AC-3: TS mirror, fixture, index updated.

## Verification Commands
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_112.py -v
```

## Test Mapping
| AC | Test Function | File |
|----|--------------|------|
| AC-1 | test_asset_sourcing_entry_minimal | tests/unit/contracts/test_spec_a_112.py |
| AC-1 | test_asset_sourcing_entry_full | tests/unit/contracts/test_spec_a_112.py |
| AC-2 | test_asset_sourcing_entry_status_constrained | tests/unit/contracts/test_spec_a_112.py |
