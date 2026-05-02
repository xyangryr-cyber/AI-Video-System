# [SPEC-GAPFIX-016] types/events.ts 同步 EventType 枚举

## Metadata
- **task_id**: SPEC-GAPFIX-016
- **spec_ref**: Design Spec §4.3
- **depends_on**: [GAPFIX-002]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Update `src/frontend/types/events.ts` to import `EventType` from shared contracts instead of defining inline magic strings. Update all components that use event type strings to reference the enum.

## Allowed Files
- `src/frontend/types/events.ts`
- `src/frontend/components/**` (any files using magic event strings)
- `src/frontend/hooks/**` (any files using magic event strings)

## Forbidden Files
- `src/backend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `types/events.ts` imports `EventType` from `@shared/contracts/event_types`
- [ ] AC-2: 全局搜索无魔法字符串 `"phase.entered"`, `"task.created"` 等事件类型字面量 (或仅存在于注释/测试中)
- [ ] AC-3: `cd src/frontend && npx tsc --noEmit` 无新增类型错误

## Verification Commands
```bash
# 检查 EventType 导入
grep -rn 'EventType' src/frontend/types/events.ts

# 检查魔法字符串
grep -rn '"phase\.\|"task\.\|"review\.\|"artifact\.\|"error\.\|"project\.\|"preference\.\|"ws\.\|"heartbeat"' src/frontend/ || echo "No bare event type strings found (OK)"

cd src/frontend && npx tsc --noEmit 2>&1 | head -5
```

## Completion Definition
`types/events.ts` 从共享合约导入 `EventType`，组件中使用枚举值而非字面量。tsc 无新增错误。
