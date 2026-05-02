# [SPEC-C-002] Task Data Structures & State Machine

## Metadata
- **task_id**: SPEC-C-002
- **spec_ref**: SPEC-3.2, SPEC-3.6
- **depends_on**: [SPEC-A-001, SPEC-C-001]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement the 8 task types (`generate_artifact`, `regenerate_section`, `user_revision`, `review`, `research`, `verify`, `cross_check`, `user_annotation`) and the complete state machine for task_ledger.status transitions. The state machine must enforce the exact transition matrix from SPEC-3.6: any illegal transition raises `IllegalStateTransition`. Every legal transition writes to the `events` table.

## Allowed Files
- `src/backend/engine/task_types.py`
- `src/backend/engine/state_machine.py`
- `src/backend/engine/workflow_engine.py`
- `tests/unit/backend-core/test_task_types.py`
- `tests/unit/backend-core/test_state_machine.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/shared/schemas/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Task `id` follows `t_<6-digit>` monotonically increasing format
- [ ] AC-2: `review` task has no `produces_version` field; `generate_artifact` has no `target_version` field
- [ ] AC-3: 8 task types are enumerated and validated; no `await_user` type exists
- [ ] AC-4: `succeeded` -> `running` transition raises `IllegalStateTransition`
- [ ] AC-5: `failed` -> `queued` transition raises `IllegalStateTransition`
- [ ] AC-6: All 10 legal transitions from the matrix pass unit tests
- [ ] AC-7: Every legal transition writes a corresponding event to the `events` table (task.started, task.completed, task.failed, etc.)
- [ ] AC-8: `review.target_version != phase.artifact_version` causes task to be set to `superseded`

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_002.py -v
ruff check src/backend/engine/task_types.py src/backend/engine/state_machine.py
mypy src/backend/engine/task_types.py src/backend/engine/state_machine.py --strict
```

## Completion Definition
All 8 task types defined with correct field constraints. State machine enforces the full transition matrix. Illegal transitions raise exceptions. Legal transitions emit events. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_002.py | test_task_id_format_monotonic |
| AC-2 | tests/unit/backend-core/test_spec_c_002.py | test_review_no_produces_version |
| AC-2 | tests/unit/backend-core/test_spec_c_002.py | test_generate_artifact_no_target_version |
| AC-3 | tests/unit/backend-core/test_spec_c_002.py | test_eight_task_types_no_await_user |
| AC-4 | tests/unit/backend-core/test_spec_c_002.py | test_succeeded_to_running_raises |
| AC-5 | tests/unit/backend-core/test_spec_c_002.py | test_failed_to_queued_raises |
| AC-6 | tests/unit/backend-core/test_spec_c_002.py | test_all_legal_transitions |
| AC-7 | tests/unit/backend-core/test_spec_c_002.py | test_transition_writes_event |
| AC-8 | tests/unit/backend-core/test_spec_c_002.py | test_stale_review_superseded |
