# [SPEC-GAPFIX-023] TaskType docstring "8 → 17"

## Metadata
- **task_id**: SPEC-GAPFIX-023
- **spec_ref**: Design Spec §6.4
- **depends_on**: []
- **priority**: P2
- **estimated_complexity**: S

## Scope
Fix `src/backend/engine/task_types.py` docstring: change "8 canonical task types" to "17 task types" (or current actual count).

## Allowed Files
- `src/backend/engine/task_types.py`

## Forbidden Files
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: docstring 不再写 "8 canonical task types"
- [ ] AC-2: docstring 反映实际 task type 数量

## Verification Commands
```bash
grep -n 'canonical\|task type' src/backend/engine/task_types.py
.venv/bin/python3 -c "from src.backend.engine.task_types import TaskType; print(f'{len(TaskType)} task types')"
```

## Completion Definition
Docstring 准确反映当前 task type 数量。Per HARNESS §4.3, docstring changes are TDD-exempt.
