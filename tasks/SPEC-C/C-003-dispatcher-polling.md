# [SPEC-C-003] Dispatcher Polling & Task Scheduling

## Metadata
- **task_id**: SPEC-C-003
- **spec_ref**: SPEC-3.3
- **depends_on**: [SPEC-A-001, SPEC-C-001, SPEC-C-002]
- **priority**: P0
- **estimated_complexity**: S

## Scope
Implement the Dispatcher component within WorkflowEngine that polls `task_ledger` every 2 seconds, identifies `pending` tasks whose dependencies have all `succeeded`, and transitions them to `queued` in `created_at` order. Enforce single-concurrency: at most 1 task in `running` state at any time.

## Allowed Files
- `src/backend/engine/dispatcher.py`
- `src/backend/engine/workflow_engine.py`
- `tests/unit/backend-core/test_dispatcher.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/backend/workers/**` (owned by SPEC-B)

## Acceptance Criteria
- [ ] AC-1: 3 pending tasks with satisfied dependencies are dispatched in `created_at` order
- [ ] AC-2: At most 1 task in `running` state at any moment
- [ ] AC-3: Polling interval is configurable, defaults to 2 seconds
- [ ] AC-4: Tasks with unsatisfied dependencies remain `pending`
- [ ] AC-5: `superseded` tasks are skipped by Dispatcher

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_003.py -v
ruff check src/backend/engine/dispatcher.py
mypy src/backend/engine/dispatcher.py --strict
```

## Completion Definition
Dispatcher correctly polls, orders by created_at, respects dependency resolution, enforces single-concurrency, and skips superseded tasks. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_003.py | test_dispatch_order_by_created_at |
| AC-2 | tests/unit/backend-core/test_spec_c_003.py | test_max_one_running_task |
| AC-3 | tests/unit/backend-core/test_spec_c_003.py | test_polling_interval_configurable |
| AC-4 | tests/unit/backend-core/test_spec_c_003.py | test_unsatisfied_deps_stay_pending |
| AC-5 | tests/unit/backend-core/test_spec_c_003.py | test_superseded_tasks_skipped |
