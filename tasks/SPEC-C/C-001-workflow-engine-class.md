# [SPEC-C-001] WorkflowEngine Single-Class Implementation

## Metadata
- **task_id**: SPEC-C-001
- **spec_ref**: SPEC-3.1
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement the `WorkflowEngine` class that consolidates FSM, TaskLedger management, Dispatcher, and EventPublisher into a single class. V1 design: single-machine, single-project simplification. All task_ledger state mutations must go through WorkflowEngine methods. EventBus is a pure-function internal component with no hidden global subscriber state.

## Allowed Files
- `src/backend/engine/workflow_engine.py`
- `src/backend/engine/__init__.py`
- `src/backend/engine/event_bus.py`
- `tests/unit/backend-core/test_workflow_engine.py`

## Forbidden Files
- `src/frontend/**`
- `src/shared/types/**` (owned by SPEC-A)
- `src/shared/schemas/**` (owned by SPEC-A)
- `src/backend/api/**`

## Acceptance Criteria
- [ ] AC-1: All task_ledger state changes occur exclusively through WorkflowEngine methods; no external code writes directly to task_ledger table
- [ ] AC-2: EventBus is a pure function (no instance variables storing subscriber state, no global registry)
- [ ] AC-3: WorkflowEngine reads from `projects`, `phases`, and `task_ledger` tables as inputs
- [ ] AC-4: WorkflowEngine writes to `phases` (status/artifact_version), `task_ledger` (new tasks/status changes), and `events` table
- [ ] AC-5: Class file stays under 400 lines (split helpers into submodules if needed)

## Verification Commands
```bash
pytest tests/unit/backend-core/test_spec_c_001.py -v
ruff check src/backend/engine/
mypy src/backend/engine/ --strict
```

## Completion Definition
WorkflowEngine class exists with public methods for all task_ledger mutations. EventBus is stateless. No direct task_ledger writes exist outside the engine. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/backend-core/test_spec_c_001.py | test_state_change_only_via_engine |
| AC-2 | tests/unit/backend-core/test_spec_c_001.py | test_event_bus_no_instance_state |
| AC-2 | tests/unit/backend-core/test_spec_c_001.py | test_event_bus_pure_function |
| AC-3 | tests/unit/backend-core/test_spec_c_001.py | test_engine_reads_projects_phases_ledger |
| AC-4 | tests/unit/backend-core/test_spec_c_001.py | test_engine_writes_events_on_mutation |
| AC-5 | tests/unit/backend-core/test_spec_c_001.py | test_engine_file_line_count_under_400 |
