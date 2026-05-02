# [SPEC-E-104] ChartConfirmDialog

## Metadata
- **task_id**: SPEC-E-104
- **spec_ref**: SPEC-E §E-BDD-5
- **depends_on**: [SPEC-A-103, SPEC-C-105]
- **priority**: P0
- **estimated_complexity**: L

## Scope
实现 ChartConfirmDialog：限制每轮澄清最多 2 个问题（按优先级排序）、根据数据来源验证状态显示徽章并控制确认按钮可用性、颜色选择器锁定 style_lock.color_palette，并正确反映 5 状态切换。

## Allowed Files
- `src/frontend/components/ChartConfirmDialog.tsx`
- `src/frontend/components/chart/ClarificationQuestionList.tsx`
- `src/frontend/components/chart/DataSourceBadge.tsx`
- `src/frontend/components/chart/AxisEditor.tsx`
- `src/frontend/components/chart/StyleEditor.tsx`
- `tests/e2e/chart_confirm_dialog.spec.ts`

## Acceptance Criteria
- [ ] AC-1: 每次澄清最多 2 问题;优先级 time_range/granularity > entity > unit
- [ ] AC-2: 未验证来源徽章红色且"确认渲染"按钮禁用
- [ ] AC-3: 颜色选择器限制在 style_lock.color_palette 内
- [ ] AC-4: 5 状态切换 UI 变化正确反映

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_104.py -v
npx playwright test tests/e2e/chart_confirm_dialog.spec.ts
```

## Completion Definition
ChartConfirmDialog 在澄清问题节流与优先级、未验证拦截、调色板锁定与 5 状态 UI 切换四项验收均通过 e2e 验证。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_104.py | clarification_limits_two_questions_by_priority |
| AC-2 | tests/unit/frontend/test_spec_e_104.py | unverified_source_badge_red_and_confirm_disabled |
| AC-3 | tests/unit/frontend/test_spec_e_104.py | color_picker_restricted_to_style_lock_palette |
| AC-4 | tests/unit/frontend/test_spec_e_104.py | five_state_transitions_render_correct_ui |
