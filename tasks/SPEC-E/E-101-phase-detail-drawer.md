# [SPEC-E-101] PhaseDetailDrawer 7 分块

## Metadata
- **task_id**: SPEC-E-101
- **spec_ref**: SPEC-E §E-BDD-2
- **depends_on**: [SPEC-A-102, SPEC-C-102]
- **priority**: P0
- **estimated_complexity**: M
- **bdd_tags**: [@navigation]

## Scope
实现 PhaseDetailDrawer 抽屉，按 7 个固定分块（产物列表、Reviewer 结果、Gate 结果、Claim 快照、Preference 快照、Diff 视图、操作历史时间线）渲染历史阶段详情，并支持只读态及"从此阶段继续修改"回退操作。

## Allowed Files
- `src/frontend/components/PhaseDetailDrawer.tsx`
- `src/frontend/components/phase_detail/ArtifactList.tsx`
- `src/frontend/components/phase_detail/ReviewerResults.tsx`
- `src/frontend/components/phase_detail/GateResult.tsx`
- `src/frontend/components/phase_detail/ClaimSnapshot.tsx`
- `src/frontend/components/phase_detail/PreferenceSnapshot.tsx`
- `src/frontend/components/phase_detail/DiffView.tsx`
- `src/frontend/components/phase_detail/OperationHistoryTimeline.tsx`
- `tests/e2e/phase_detail_drawer.spec.ts`

## Acceptance Criteria
- [ ] AC-1: 7 分块全部渲染;缺失分块显示空态(不崩)
- [ ] AC-2: read_only 态所有编辑入口禁用
- [ ] AC-3: "从此阶段继续修改" 按钮触发二次确认 + POST /revert
- [ ] AC-4: revert 成功后 current_phase 回退,latest_reached_phase 不变

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_101.py -v
npx playwright test tests/e2e/phase_detail_drawer.spec.ts
```

## Completion Definition
PhaseDetailDrawer 在 7 分块完整、缺失态、只读禁用、回退确认与回退后状态字段更新四个维度均通过 e2e 验证。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_101.py | renders_all_seven_blocks_with_empty_state_fallback |
| AC-2 | tests/unit/frontend/test_spec_e_101.py | disables_edit_entries_in_read_only_mode |
| AC-3 | tests/unit/frontend/test_spec_e_101.py | revert_button_triggers_confirm_and_post |
| AC-4 | tests/unit/frontend/test_spec_e_101.py | revert_rolls_back_current_phase_only |
