# [SPEC-A-002] Candidate & ProjectState Contracts

## Metadata
- **task_id**: SPEC-A-002
- **spec_ref**: SPEC-0A.2, SPEC-0A.3
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Define the `Candidate` interface and `ProjectState` response contract. ProjectState is the single most important API response shape -- it drives frontend state restoration. Includes the computed fields (review_status, artifact_url, system_status aggregation) documentation as code comments.

## Allowed Files
- `src/shared/types/candidate.ts`
- `src/shared/types/project_state.ts`
- `src/shared/schemas/candidate.py`
- `src/shared/schemas/project_state.py`
- `tests/unit/contracts/test_candidate_project_state.py`

## Forbidden Files
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: `Candidate` TypeScript interface has all 8 fields (candidate_id, preview_url, preview_type enum, style_tags, description, is_recommended, adjustable_params, rationale)
- [ ] AC-2: `Candidate` Pydantic model validates candidate_id starts with `cand_`, preview_type is one of 4 enum values, candidates count ≤3 enforced by container validator
- [ ] AC-3: `ProjectState` TypeScript interface matches SPEC-0A.3 exactly (project, phases[], active_tasks[], preferences, system_status)
- [ ] AC-4: `ProjectState` Pydantic model includes docstrings documenting computed fields (review_status from task_ledger, artifact_url from artifact_path, system_status from system_status table)
- [ ] AC-5: Phase status enum covers all 5 values: pending, active, completed, skipped, invalidated
- [ ] AC-6: Phase artifact_status enum covers: ok, damaged, missing, null

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_002.py -v
mypy src/shared/schemas/candidate.py src/shared/schemas/project_state.py --strict
npx tsc --noEmit src/shared/types/candidate.ts src/shared/types/project_state.ts
```

## Completion Definition
Both Candidate and ProjectState have matching TS interfaces and Pydantic models. All enum values are validated. Computed field derivation logic is documented in code. Tests cover valid and invalid payloads.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_002.py | test_candidate_interface_fields |
| AC-2 | tests/unit/contracts/test_spec_a_002.py | test_candidate_id_prefix_validation |
| AC-2 | tests/unit/contracts/test_spec_a_002.py | test_candidate_preview_type_enum |
| AC-2 | tests/unit/contracts/test_spec_a_002.py | test_candidates_max_3 |
| AC-3 | tests/unit/contracts/test_spec_a_002.py | test_project_state_structure |
| AC-4 | tests/unit/contracts/test_spec_a_002.py | test_project_state_computed_fields_documented |
| AC-5 | tests/unit/contracts/test_spec_a_002.py | test_phase_status_enum |
| AC-6 | tests/unit/contracts/test_spec_a_002.py | test_artifact_status_enum |
