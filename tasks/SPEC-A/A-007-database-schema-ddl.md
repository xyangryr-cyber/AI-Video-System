# [SPEC-A-007] SQLite Database Schema DDL (10 Tables)

## Metadata
- **task_id**: SPEC-A-007
- **spec_ref**: SPEC-1B
- **depends_on**: []
- **priority**: P0
- **estimated_complexity**: M

## Scope
Create the authoritative DDL migration file for all 10 SQLite tables: projects, phases, task_ledger, async_tasks, events, preferences, agent_call_log, system_status, financial_data_cache, preference_snapshots. Include all CHECK constraints, UNIQUE constraints, foreign keys, and default values exactly as specified. Also define the task_ledger.params JSON schema per task type as a validation module.

## Allowed Files
- `src/backend/db/schema.sql`
- `src/backend/db/migrations/001_initial.sql`
- `src/shared/schemas/task_params.py`
- `src/shared/types/task_params.ts`
- `tests/unit/contracts/test_database_schema.py`

## Forbidden Files
- `src/backend/api/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: DDL defines exactly 10 tables with names matching spec
- [ ] AC-2: projects.status CHECK constraint enforces (active, completed, archived, deleted)
- [ ] AC-3: phases.status CHECK constraint enforces (pending, active, completed, skipped, invalidated)
- [ ] AC-4: phases has UNIQUE(project_id, phase_num) constraint
- [ ] AC-5: task_ledger.type CHECK constraint enforces all 8 task types
- [ ] AC-6: task_ledger.status CHECK constraint enforces all 7 statuses
- [ ] AC-7: async_tasks.progress CHECK constraint enforces BETWEEN 0 AND 100
- [ ] AC-8: agent_call_log.tokens CHECK constraint enforces tokens > 0
- [ ] AC-9: financial_data_cache has UNIQUE(symbol, granularity, date_range_start, date_range_end)
- [ ] AC-10: All timestamp defaults use strftime('%Y-%m-%dT%H:%M:%fZ','now')
- [ ] AC-11: task_params validation module covers all 8 type-specific param schemas with required fields
- [ ] AC-12: Loading DDL into in-memory SQLite succeeds without errors

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_007.py -v
sqlite3 :memory: < src/backend/db/schema.sql && echo "DDL OK"
mypy src/shared/schemas/task_params.py --strict
```

## Completion Definition
DDL file creates all 10 tables in SQLite without error. All CHECK/UNIQUE/FK constraints are present. Task params validation covers all 8 types. Tests verify constraint enforcement by attempting invalid inserts.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_007.py | test_exactly_10_tables |
| AC-2 | tests/unit/contracts/test_spec_a_007.py | test_projects_status_check |
| AC-3 | tests/unit/contracts/test_spec_a_007.py | test_phases_status_check |
| AC-4 | tests/unit/contracts/test_spec_a_007.py | test_phases_unique_project_phase |
| AC-5 | tests/unit/contracts/test_spec_a_007.py | test_task_ledger_type_check |
| AC-6 | tests/unit/contracts/test_spec_a_007.py | test_task_ledger_status_check |
| AC-7 | tests/unit/contracts/test_spec_a_007.py | test_async_tasks_progress_check |
| AC-8 | tests/unit/contracts/test_spec_a_007.py | test_agent_call_log_tokens_check |
| AC-9 | tests/unit/contracts/test_spec_a_007.py | test_financial_cache_unique_constraint |
| AC-10 | tests/unit/contracts/test_spec_a_007.py | test_timestamp_defaults |
| AC-11 | tests/unit/contracts/test_spec_a_007.py | test_task_params_all_8_types |
| AC-12 | tests/unit/contracts/test_spec_a_007.py | test_ddl_loads_successfully |
