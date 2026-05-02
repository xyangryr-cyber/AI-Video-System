# [SPEC-A-109] PolishedScriptArtifact (v3.18 D7)

## Metadata
- **task_id**: SPEC-A-109
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D7
- **depends_on**: [SPEC-A-105]

## Scope
Define a new `PolishedScriptArtifact` Pydantic model with `style_applied: Optional[str]` (the style label selected from StyleLock/Candidate at P3, e.g., "亲切科普型"). Word count and duration are computable from the timeline (rejected per D7 disposition); only the style label belongs on the polished-script artifact itself.

## Acceptance Criteria
- [ ] AC-1: PolishedScriptArtifact has `style_applied: Optional[str]`.
- [ ] AC-2: TS mirror exists.
- [ ] AC-3: Fixture demonstrates a populated style label.

## Verification Commands
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_109.py -v
```

## Test Mapping
| AC | Test Function | File |
|----|--------------|------|
| AC-1 | test_polished_script_artifact_accepts_style_applied | tests/unit/contracts/test_spec_a_109.py |
| AC-1 | test_polished_script_artifact_omits_style_applied | tests/unit/contracts/test_spec_a_109.py |
