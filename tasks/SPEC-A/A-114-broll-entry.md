# [SPEC-A-114] BRollEntry (v3.18 D12)

## Metadata
- **task_id**: SPEC-A-114
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D12
- **depends_on**: [SPEC-A-105]

## Scope
B-Roll item metadata (P10): file, duration, match label, license, optional source URL. Drives gallery + legal-attribution display.

## Acceptance Criteria
- [ ] AC-1: BRollEntry has file_name, duration_sec, match_label, license, source_url (Optional).

## Verification Commands
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_114.py -v
```

## Test Mapping
| AC | Test Function | File |
|----|--------------|------|
| AC-1 | test_broll_entry_full | tests/unit/contracts/test_spec_a_114.py |
| AC-1 | test_broll_entry_minimal_no_source_url | tests/unit/contracts/test_spec_a_114.py |
