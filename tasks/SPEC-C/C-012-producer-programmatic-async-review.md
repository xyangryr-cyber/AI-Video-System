# [SPEC-C-012] Producer Programmatic Steps & Async Review Execution

## Metadata
- **task_id**: SPEC-C-012
- **spec_ref**: SPEC-5.6, SPEC-5.8
- **depends_on**: [SPEC-A-001, SPEC-C-009, SPEC-C-010]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement 5 deterministic (non-LLM) Producer sub-steps: TTS SSML generation, BGM volume envelope, SFX timeline, RoughCut parameters, and word_count calculation. These must be 100% reproducible (same input = same output, verified by 10-run hash comparison). Also implement async review execution: after Producer completes, artifact is immediately readable while review runs in the background. `review_status` is computed at API layer from `task_ledger` state (not a DB field).

## Allowed Files
- `src/backend/agents/producer_steps.py`
- `src/backend/engine/workflow_engine.py`
- `tests/unit/backend-core/test_producer_steps.py`
- `tests/unit/backend-core/test_async_review.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/backend/workers/**` (owned by SPEC-B)

## Acceptance Criteria
- [ ] AC-1: 5 programmatic steps produce identical output across 10 runs (hash comparison)
- [ ] AC-2: 5 programmatic steps make zero LLM API calls
- [ ] AC-3: After Producer completes, artifact is immediately readable (review task exists as pending in task_ledger)
- [ ] AC-4: Review completion emits `review.completed` WebSocket event
- [ ] AC-5: `review_status` is computed from task_ledger, not stored as a DB column

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_012.py -v
ruff check src/backend/agents/producer_steps.py
mypy src/backend/agents/producer_steps.py --strict
```

## Completion Definition
5 programmatic steps are deterministic and LLM-free. Async review runs in background without blocking artifact access. review_status computed dynamically. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_012.py | test_deterministic_output_10_runs |
| AC-2 | tests/unit/backend-core/test_spec_c_012.py | test_no_llm_calls |
| AC-3 | tests/unit/backend-core/test_spec_c_012.py | test_artifact_readable_during_review |
| AC-4 | tests/unit/backend-core/test_spec_c_012.py | test_review_complete_emits_ws_event |
| AC-5 | tests/unit/backend-core/test_spec_c_012.py | test_review_status_computed_not_stored |
