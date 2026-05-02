# [SPEC-E-014] P7A Shot × Material 矩阵 + chart 时间范围/axis_spec 确认卡

## Metadata
- **task_id**: SPEC-E-014
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §E-AUDP7A-4
- **delta_id**: PRD-DELTA-06 / PRD-DELTA-07 / TECH-DELTA-08
- **depends_on**: [SPEC-A-015, SPEC-A-016, SPEC-E-015]
- **priority**: P0
- **estimated_complexity**: L

## Scope
新增 SPEC-2.X.7A Phase 7A 预览组件章节：Shot×Material 矩阵（行=shot，列=material，单元格按 verification_status 4 色）+ 详情弹窗（rationale/source/evidence/重抓按钮）+ 图表类 shot 的 ChartMaterialConfirmCard（axis_spec 时间范围与 y_axis 范围确认）。

## Allowed Files
- `src/frontend/components/phase7a/Phase7AMatrix.tsx` (NEW)
- `src/frontend/components/phase7a/MaterialDetailDrawer.tsx` (NEW)
- `src/frontend/components/phase7a/ChartMaterialConfirmCard.tsx` (NEW)
- `src/frontend/api/material_actions.ts` (NEW；refetch + supplement)
- `tests/unit/frontend/phase7a/*.test.tsx` (NEW)
- `tests/integration/frontend/p7a_matrix_e2e.spec.ts` (NEW Playwright)

## Forbidden Files
- `src/shared/**`
- `src/backend/**`
- `src/frontend/components/phase{4,5,6}/**`

## Acceptance Criteria
- [ ] AC-1：矩阵渲染：shots × materials 网格；状态色：pending=灰 / verified=绿 / rejected=橙 / missing=红（CSS class 或 data-status 验证）
- [ ] AC-2：missing 单元格点击 → MaterialDetailDrawer 弹出 + "重抓" 按钮触发 `on_request_refetch(material_id)` callback
- [ ] AC-3：ChartMaterialConfirmCard 展示 axis_spec.x_axis.range（时间区间）+ y_axis.unit / min / max；用户点 "请求修改" → `on_request_change` 携带 ChartChangeRequest
- [ ] AC-4：on_user_supplement 触发 → POST `supplement_material`（task_ledger 写一条 supplement_material 类型记录；本任务断言 API 调用，task_ledger 行入库由后端 v3.16 路径承担）
- [ ] AC-5：a11y：矩阵 cell 含 `role="gridcell"` + 状态徽章 `aria-label`（如"已验证"）；矩阵容器含 `role="grid"`
- [ ] AC-6：v3.16 StoryboardShotAnchor 的 anchor_text 在 shot 行显示（hover 全文），shot_id 与 material.shot_id 一致

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_014.py -v
npx playwright test tests/integration/frontend/p7a_matrix_e2e.spec.ts
npx tsc --noEmit src/frontend/components/phase7a/*.tsx
```

## Completion Definition
矩阵 + Drawer + ChartConfirmCard + API client + 全部 6 条 AC PASS + Playwright 覆盖。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_014.py | renders_grid_with_status_colors |
| AC-2 | tests/unit/frontend/test_spec_e_014.py | missing_cell_opens_drawer_and_refetch |
| AC-3 | tests/unit/frontend/test_spec_e_014.py | renders_axis_spec_and_change_request |
| AC-4 | tests/unit/frontend/test_spec_e_014.py | supplement_material_calls_api |
| AC-5 | tests/unit/frontend/test_spec_e_014.py | a11y_grid_role_and_cell_aria |
| AC-6 | tests/unit/frontend/test_spec_e_014.py | shows_anchor_text_per_shot_row |

## §23.9 验收门禁映射
- 第 10 行：前端 shot_material_bindings 可用（P7A 部分）
