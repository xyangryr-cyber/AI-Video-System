# [SPEC-E-102] Claim 工作台(替代 SPEC-2.7 DataVerificationPanel)

## Metadata
- **task_id**: SPEC-E-102
- **spec_ref**: SPEC-E §E-BDD-3
- **depends_on**: [SPEC-A-100, SPEC-C-103]
- **priority**: P0
- **estimated_complexity**: L

## Scope
构建 Claim 工作台，提供 4 维筛选、4 类行级操作、Top 统计条与 hard blocking 徽章，替代 v3.15 的 DataVerificationPanel。风险 R-2：Coverage Summary 已标 supersedes，实现时必须同步删除 v3.15 旧组件 `DataVerificationPanel.tsx` 的所有引用，避免残留双入口。

## Allowed Files
- `src/frontend/components/ClaimWorkbench.tsx`
- `src/frontend/components/claim/ClaimFilterBar.tsx`
- `src/frontend/components/claim/ClaimRowActions.tsx`
- `src/frontend/components/claim/TopStatsBar.tsx`
- `src/frontend/components/claim/BlockingBadge.tsx`
- `src/frontend/components/DataVerificationPanel.tsx`
- `tests/e2e/claim_workbench.spec.ts`

## Acceptance Criteria
- [ ] AC-1: 4 筛选维度组合可筛出正确子集
- [ ] AC-2: 4 行级操作均正确触发对应 action
- [ ] AC-3: hard blocking unverified > 0 时右上角徽章显示红色
- [ ] AC-4: 表格/卡片视图切换保持筛选态

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_102.py -v
npx playwright test tests/e2e/claim_workbench.spec.ts
```

## Completion Definition
ClaimWorkbench 替代旧 DataVerificationPanel 上线，4 维筛选/4 行操作/红色阻塞徽章/视图切换保留筛选态全部通过 e2e 验证，且 v3.15 旧组件引用已被清理。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_102.py | filter_bar_four_dimensions_returns_correct_subset |
| AC-2 | tests/unit/frontend/test_spec_e_102.py | row_actions_trigger_corresponding_actions |
| AC-3 | tests/unit/frontend/test_spec_e_102.py | blocking_badge_turns_red_when_hard_unverified_gt_zero |
| AC-4 | tests/unit/frontend/test_spec_e_102.py | view_toggle_preserves_filter_state |
