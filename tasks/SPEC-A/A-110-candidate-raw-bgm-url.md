# [SPEC-A-110] Candidate + raw_bgm_url (v3.18 D8)

## Metadata
- **task_id**: SPEC-A-110
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D8
- **depends_on**: [SPEC-A-105]

## Scope
Add `raw_bgm_url: Optional[str]` to `Candidate`. SPEC-E-012 P5 BGM card requires a dual-URL pattern: `preview_url` for the trimmed preview clip, `raw_bgm_url` for the full-length downloadable track.

## Acceptance Criteria
- [ ] AC-1: Candidate accepts `raw_bgm_url` as Optional[str].
- [ ] AC-2: TS mirror has `raw_bgm_url?: string`.
- [ ] AC-3: Fixture has BGM candidates demonstrating the field.

## Verification Commands
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_110.py -v
```

## Test Mapping
| AC | Test Function | File |
|----|--------------|------|
| AC-1 | test_candidate_accepts_raw_bgm_url | tests/unit/contracts/test_spec_a_110.py |
| AC-1 | test_candidate_omits_raw_bgm_url_when_not_provided | tests/unit/contracts/test_spec_a_110.py |
