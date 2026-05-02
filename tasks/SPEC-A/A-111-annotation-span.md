# [SPEC-A-111] AnnotationSpan (v3.18 D9)

## Metadata
- **task_id**: SPEC-A-111
- **spec_ref**: docs/SPEC_REVISION_REQ_v3.18_PROTOTYPE_DELTA.md D9
- **depends_on**: [SPEC-A-105]

## Scope
Define `AnnotationSpan` for P6 SFX/annotation tooltips. Includes `narrative_role` (E-013 AC-1 requirement that the prototype is missing).

## Acceptance Criteria
- [ ] AC-1: AnnotationSpan has fields: span_id, text_range (tuple int,int), effect, rationale, narrative_role.
- [ ] AC-2: TS mirror exists.
- [ ] AC-3: Fixture demonstrates a span with all fields populated.

## Verification Commands
```bash
.venv/bin/python -m pytest tests/unit/contracts/test_spec_a_111.py -v
```

## Test Mapping
| AC | Test Function | File |
|----|--------------|------|
| AC-1 | test_annotation_span_accepts_all_fields | tests/unit/contracts/test_spec_a_111.py |
| AC-1 | test_annotation_span_requires_narrative_role | tests/unit/contracts/test_spec_a_111.py |
