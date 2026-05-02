# [SPEC-GAPFIX-032] 12 Phase preview 组件补全

## Metadata
- **task_id**: SPEC-GAPFIX-032
- **spec_ref**: Design Spec §8.4
- **depends_on**: [GAPFIX-016]
- **priority**: P2
- **estimated_complexity**: L

## Scope
Complete the 12 Phase preview components in `src/frontend/components/preview/`. Currently only 4/12 exist (P4/P5/P6/P7A). Create the missing 8: P0, P1, P2, P3, P7B, P8, P9, P10, P11 (need to verify exact list).

## Allowed Files
- `src/frontend/components/preview/Phase*.tsx`
- `src/frontend/components/preview/index.ts`

## Forbidden Files
- `src/backend/**`
- `HARNESS.md`

## Acceptance Criteria
- [ ] AC-1: `ls src/frontend/components/preview/Phase*.tsx | wc -l` 输出 12
- [ ] AC-2: 每个组件接收 `projectId: string` 作为 props
- [ ] AC-3: 每个组件渲染 phase-specific UI 骨架 (不要求完整实现，但不能是 `<div />`)
- [ ] AC-4: `cd src/frontend && npx vitest run` 通过
- [ ] AC-5: `cd src/frontend && npx tsc --noEmit` 无新增错误

## Verification Commands
```bash
ls src/frontend/components/preview/Phase*.tsx | wc -l  # 期望 12
cd src/frontend && npx vitest run --reporter=verbose 2>&1 | tail -5
```

## Completion Definition
12 个 Phase preview 组件存在，vitest 通过，tsc 无新增错误。
