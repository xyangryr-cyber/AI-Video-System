# [SPEC-E-105] PreferenceWritebackCard + SafetyResponseCard

## Metadata
- **task_id**: SPEC-E-105
- **spec_ref**: SPEC-E §E-BDD-6
- **depends_on**: [SPEC-C-100, SPEC-C-102]
- **priority**: P0
- **estimated_complexity**: M

## Scope
实现 PreferenceWritebackCard（三栏对比 + 批量保存）与 SafetyResponseCard（分类标签 + 模板话术 + 决策依据折叠区），保证不暴露原始 user input 并满足 a11y 键盘可达。

## Allowed Files
- `src/frontend/components/PreferenceWritebackCard.tsx`
- `src/frontend/components/SafetyResponseCard.tsx`
- `src/frontend/hooks/usePreferenceWriteback.ts`
- `tests/e2e/preference_safety_cards.spec.ts`

## Acceptance Criteria
- [ ] AC-1: 三栏对比 `当前 vs 历史 vs 推荐`;批量勾选 + 一键保存
- [ ] AC-2: SafetyResponseCard 显示分类标签 + 模板话术,不显示原始 user input
- [ ] AC-3: "为什么这个回复"折叠区展示 policy 决策依据(template_id)
- [ ] AC-4: a11y:aria-label / 键盘导航可用

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_105.py -v
npx playwright test tests/e2e/preference_safety_cards.spec.ts
```

## Completion Definition
两张卡片在三栏对比批量回写、安全模板替换、policy 决策可解释、键盘 a11y 四项验收均通过 e2e 验证。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_105.py | three_column_compare_and_batch_save |
| AC-2 | tests/unit/frontend/test_spec_e_105.py | safety_card_shows_template_not_raw_input |
| AC-3 | tests/unit/frontend/test_spec_e_105.py | why_this_reply_collapsible_shows_template_id |
| AC-4 | tests/unit/frontend/test_spec_e_105.py | a11y_aria_label_and_keyboard_navigation |
