# [SPEC-GAPFIX-002] event_types.ts — TypeScript 版本

## Metadata
- **task_id**: SPEC-GAPFIX-002
- **spec_ref**: Design Spec §2.2
- **depends_on**: [GAPFIX-001]
- **priority**: P0
- **estimated_complexity**: S

## Scope
Define 17 WebSocket event types as a TypeScript const object in `src/shared/contracts/event_types.ts`, mirroring `event_types.py`.

## Allowed Files
- `src/shared/contracts/event_types.ts`
- `tests/unit/contracts/test_event_types_crosslang.py`

## Forbidden Files
- `src/backend/**`
- `src/frontend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: TypeScript `EventType` const 包含恰好 17 个成员
- [ ] AC-2: 成员名称与 Python `EventType` enum 完全一致 (跨语言一致性)
- [ ] AC-3: TypeScript 类型导出可被前端 `types/events.ts` 导入

## Verification Commands
```bash
# 跨语言一致性测试
.venv/bin/python3 -m pytest tests/unit/contracts/test_event_types_crosslang.py -v
# TypeScript 编译
cd src/frontend && npx tsc --noEmit src/shared/contracts/event_types.ts
```

## Completion Definition
`EventType` TypeScript const 存在，17 个成员与 Python enum 完全一致，跨语言测试通过。

## Test Mapping
| AC | Test Function |
|----|---------------|
| AC-1 | test_ts_event_type_has_17_members |
| AC-2 | test_py_and_ts_event_types_identical |
| AC-3 | test_ts_event_type_importable |
