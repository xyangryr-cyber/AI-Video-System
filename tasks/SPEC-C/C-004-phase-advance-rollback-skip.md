# [SPEC-C-004] Phase Advance, Rollback, Skip & Idempotency

## Metadata
- **task_id**: SPEC-C-004
- **spec_ref**: SPEC-3.4, SPEC-3.7
- **depends_on**: [SPEC-A-001, SPEC-C-001, SPEC-C-002]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement phase advance (requires all tasks terminal + GateKeeper pass + user confirm), rollback (invalidates downstream phases), skip (checks only "no in-progress tasks" and "preferences confirmed"), and advance endpoint idempotency (optimistic locking, 409 on concurrent gate check, 200 on already-advanced).

## Allowed Files
- `src/backend/engine/workflow_engine.py`
- `src/backend/engine/phase_ops.py`
- `tests/unit/backend-core/test_phase_advance.py`
- `tests/unit/backend-core/test_phase_rollback.py`
- `tests/unit/backend-core/test_phase_skip.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/backend/api/**` (endpoint wiring is separate)

## Acceptance Criteria
- [ ] AC-1: Rollback to Phase X marks Phase X+1 through current phase artifacts as `invalidated`
- [ ] AC-2: Skip does not require artifact existence or review pass
- [ ] AC-3: Skip requires no in-progress tasks and preferences_confirmed_at is set
- [ ] AC-4: Rollback shows impact analysis (number of affected segments) before execution
- [ ] AC-5: Duplicate POST advance within 1s returns 200 (already advanced) or 409 (gate in progress), never re-executes gate
- [ ] AC-6: Optimistic lock `UPDATE projects SET current_phase=? WHERE project_id=? AND current_phase=?` with affected_rows=0 returns current state, not error
- [ ] AC-7: Concurrent gate check returns 409 with `EVID_2002` error code

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_004.py -v
ruff check src/backend/engine/phase_ops.py
mypy src/backend/engine/phase_ops.py --strict
```

## Completion Definition
Advance/rollback/skip logic fully implemented with idempotency guarantees. Optimistic locking prevents concurrent advances. All edge cases tested. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_004.py | test_rollback_invalidates_downstream |
| AC-2 | tests/unit/backend-core/test_spec_c_004.py | test_skip_no_artifact_ok |
| AC-3 | tests/unit/backend-core/test_spec_c_004.py | test_skip_requires_no_running_and_prefs |
| AC-4 | tests/unit/backend-core/test_spec_c_004.py | test_rollback_impact_analysis |
| AC-5 | tests/unit/backend-core/test_spec_c_004.py | test_advance_idempotent_duplicate |
| AC-6 | tests/unit/backend-core/test_spec_c_004.py | test_advance_optimistic_lock_conflict |
| AC-7 | tests/unit/backend-core/test_spec_c_004.py | test_advance_concurrent_gate_409 |
