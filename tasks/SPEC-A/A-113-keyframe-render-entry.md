# [SPEC-A-113] KeyframeRenderEntry (v3.18 D11)

## Metadata
- **task_id**: SPEC-A-113
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D11
- **depends_on**: [SPEC-A-105]

## Scope
Per-shot keyframe render status (P9 agent output): render status enum + filename + thumbnail URL.

## Acceptance Criteria
- [ ] AC-1: KeyframeRenderEntry: shot_id, render_status, file_name (Optional), thumbnail_url (Optional).
- [ ] AC-2: render_status is Literal["pending_broll","rendered"].

## Verification Commands
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_113.py -v
```

## Test Mapping
| AC | Test Function | File |
|----|--------------|------|
| AC-1 | test_keyframe_render_entry_pending | tests/unit/contracts/test_spec_a_113.py |
| AC-1 | test_keyframe_render_entry_rendered | tests/unit/contracts/test_spec_a_113.py |
| AC-2 | test_keyframe_render_status_constrained | tests/unit/contracts/test_spec_a_113.py |
