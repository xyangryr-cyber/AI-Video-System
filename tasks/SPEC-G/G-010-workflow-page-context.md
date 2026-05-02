# [SPEC-G-010] WorkflowPage 上下文状态对齐

## Metadata
- **task_id**: SPEC-G-010
- **spec_ref**: SPEC-G4.1
- **depends_on**: []
- **priority**: P1
- **estimated_complexity**: S
- **TDD 起点**: `navigation.feature` "打开项目后自动展示最新阶段" 当前 FAIL（视为 RED）→ 检查前端实现或修复 step assertion → scenario PASS（GREEN）

## Scope
BDD 场景"打开项目后自动展示最新阶段"因 WorkflowPage 缺少 task/dialog/chat 上下文而失败。需要检查前端实现: 若 WorkflowPage 已实现但 BDD assertion 过严，则更新 step；若前端确实缺上下文，则补充实现。

**判定标准**（per SPEC-G4.1）: 只有在确认 SPEC-E 已完成对应组件 AC 时才可放松断言；否则优先补前端实现。避免"放松断言"成为绕过 SPEC-E AC 的便捷出口。

## Allowed Files
- `src/frontend/components/WorkflowPage.tsx`
- `tests/integration/bdd/steps/navigation_steps.py`

## Forbidden Files
- `src/backend/**`
- `docs/specs/**`

## Acceptance Criteria
- [ ] AC-1: BDD 场景 "打开项目后自动展示最新阶段" → PASS
- [ ] AC-2: WorkflowPage 正确展示 `project_state.latest_reached_phase` 的交互上下文（如仅 relax assertion 则需写明 SPEC-E 对应 AC 已满足的证据）
- [ ] AC-3: `npx tsc --noEmit` clean
- [ ] AC-4: 前端测试无回归

## Verification Commands
```bash
pytest tests/integration/bdd/test_navigation_bdd.py -v
npx tsc --noEmit
cd src/frontend && npx vitest run --reporter=verbose
```

## Completion Definition
`navigation.feature` 的 "打开项目后自动展示最新阶段" 场景通过。完成后追加一行 commit 到 `PROGRESS.md`。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/integration/bdd/features/navigation.feature | 打开项目后自动展示最新阶段 |
