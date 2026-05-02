# [SPEC-A-008] Table Read/Write Ownership Registry

## Metadata
- **task_id**: SPEC-A-008
- **spec_ref**: SPEC-1B (table ownership table)
- **depends_on**: [SPEC-A-007]
- **priority**: P1
- **estimated_complexity**: S

## Scope
Codify the table-level read/write ownership from the SPEC-1B ownership table as a machine-readable registry. Each of the 10 tables has defined writers, write triggers, and readers. This registry enables runtime enforcement (e.g., asserting that only WorkflowEngine writes to phases) and serves as documentation for code reviews.

## Allowed Files
- `src/shared/contracts/table_ownership.py`
- `src/shared/contracts/table_ownership.ts`
- `tests/unit/contracts/test_table_ownership.py`

## Forbidden Files
- `src/backend/db/**`
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: Registry covers all 10 tables with writer, write_trigger, and reader fields
- [ ] AC-2: projects table: writer=API, readers=[frontend, WorkflowEngine]
- [ ] AC-3: phases table: writer=WorkflowEngine, readers=[frontend, GateKeeper]
- [ ] AC-4: task_ledger table: writer=WorkflowEngine, readers=[Dispatcher, frontend, GateKeeper]
- [ ] AC-5: events table: writer=[API, WorkflowEngine], readers=[frontend, WS broadcast]
- [ ] AC-6: preferences table: writer=API, readers=[frontend, ProducerAgent, PreferenceExtractor]
- [ ] AC-7: Registry exported as frozen/immutable data structure

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_008.py -v
mypy src/shared/contracts/table_ownership.py --strict
```

## Completion Definition
Ownership registry defined for all 10 tables, matching SPEC-1B exactly. Exported as immutable structure. Tests verify completeness and correct writer/reader assignments.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_008.py | test_all_10_tables_covered |
| AC-2 | tests/unit/contracts/test_spec_a_008.py | test_projects_ownership |
| AC-3 | tests/unit/contracts/test_spec_a_008.py | test_phases_ownership |
| AC-4 | tests/unit/contracts/test_spec_a_008.py | test_task_ledger_ownership |
| AC-5 | tests/unit/contracts/test_spec_a_008.py | test_events_ownership |
| AC-6 | tests/unit/contracts/test_spec_a_008.py | test_preferences_ownership |
| AC-7 | tests/unit/contracts/test_spec_a_008.py | test_registry_immutable |
