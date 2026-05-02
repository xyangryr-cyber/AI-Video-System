# [SPEC-D-001] Artifact Authority Map & Reviewer/Gate Verdict Binding

## Metadata
- **task_id**: SPEC-D-001
- **spec_ref**: SPEC-D Phase Artifact Authority Map + Reviewer/Gate/Verdict unified binding
- **depends_on**: [SPEC-A-001, SPEC-C-008]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement the Phase Artifact Authority Map registry and the unified Reviewer/Gate/Verdict binding contract. The authority map tracks each pipeline artifact's schema source, producer phase, consumer phases, and acceptance reviewer. The verdict binding enforces the standard verdict format `{verdict, notes[], blocking_issues[]}`, gate check format, and gate failure response format (`EVID_2001`).

## Allowed Files
- `src/backend/engine/artifact_authority.py`
- `src/backend/engine/verdict_binding.py`
- `src/shared/types/verdict.py`
- `src/shared/types/verdict.ts`
- `tests/unit/pipeline/test_artifact_authority.py`
- `tests/unit/pipeline/test_verdict_binding.py`

## Forbidden Files
- `src/frontend/**`
- `docs/specs/**`
- `src/shared/schemas/**` (SPEC-A owns schemas)

## Acceptance Criteria
- [ ] AC-1: Artifact authority registry covers all 9 artifacts (requirements.json, outline, polished_script, timeline.json, style_lock.json, keyframe renders, rough_cut, final_cut, emotion_curve.json)
- [ ] AC-2: Each registry entry maps producer_phase, producer_agent, consumer_phases, consumer_agents, schema_ref, acceptance_reviewer
- [ ] AC-3: Lookup by artifact name returns correct authority record
- [ ] AC-4: Reviewer verdict type enforces `{verdict: PASS|FAIL, notes: str[], blocking_issues: str[]}`
- [ ] AC-5: Gate failure response includes `EVID_2001` error code with `{failed_checks[], passed_checks[]}`
- [ ] AC-6: `review_status` computation from `task_ledger` implemented as pure function (not DB field)

## Verification Commands
```bash
pytest tests/unit/pipeline/test_spec_d_001.py -v
mypy src/backend/engine/artifact_authority.py --strict
mypy src/backend/engine/verdict_binding.py --strict
```

## Completion Definition
Artifact authority map covers all 9 artifacts with correct producer/consumer/reviewer mappings. Verdict and gate failure types are defined and validated. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/pipeline/test_spec_d_001.py | test_registry_covers_all_9_artifacts |
| AC-2 | tests/unit/pipeline/test_spec_d_001.py | test_registry_entry_has_all_fields |
| AC-3 | tests/unit/pipeline/test_spec_d_001.py | test_lookup_by_artifact_name |
| AC-4 | tests/unit/pipeline/test_spec_d_001.py | test_verdict_format_pass |
| AC-4 | tests/unit/pipeline/test_spec_d_001.py | test_verdict_format_fail_with_blocking_issues |
| AC-5 | tests/unit/pipeline/test_spec_d_001.py | test_gate_failure_response_evid_2001 |
| AC-6 | tests/unit/pipeline/test_spec_d_001.py | test_review_status_computed_from_task_ledger |
