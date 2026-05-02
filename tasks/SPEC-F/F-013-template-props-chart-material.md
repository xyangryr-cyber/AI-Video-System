# [SPEC-F-013] TemplateProps 扩展 chart_material（chart 类模板优先消费）

## Metadata
- **task_id**: SPEC-F-013
- **spec_ref**: `docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md` §F-AUDP7A-1
- **delta_id**: PRD-DELTA-07 / TECH-DELTA-06
- **depends_on**: [SPEC-A-016, SPEC-E-015]
- **priority**: P0
- **estimated_complexity**: M

## Scope
SPEC-18.1 TemplateProps 顶层接口追加可选 `chart_material?: ChartMaterialView`；SPEC-18.2 chart 类模板（line/bar/pie/candlestick/event_timeline）追加 L1 校验：渲染必须以 `chart_material.chart_spec + axis_spec` 为准；与自由 `data` 字段冲突时忽略 data。SPEC-22 失败样例追加 `chart_material_priority_violation`。

## Allowed Files
- `src/shared/types/template_props.ts` (MODIFY 追加 chart_material 可选字段)
- `src/shared/schemas/template_props.py` (MODIFY 同步)
- `src/frontend/components/charts/AnimatedLineChart.tsx` (MODIFY 优先消费 chart_material)
- `src/frontend/components/charts/AnimatedBarChart.tsx` (MODIFY)
- `src/frontend/components/charts/AnimatedPieChart.tsx` (MODIFY)
- `src/frontend/components/charts/CandlestickChart.tsx` (MODIFY)
- `src/frontend/components/charts/EventTimelineChart.tsx` (MODIFY)
- `src/frontend/render/chart_material_priority.ts` (NEW；冲突解决逻辑 + L1 校验)
- `tests/unit/frontend/render/test_chart_material_priority.test.tsx` (NEW)
- `tests/integration/frontend/test_chart_render_v317.spec.ts` (NEW)

## Forbidden Files
- `src/backend/**`
- `src/shared/types/chart_material.ts` (由 A-016 维护)
- `src/frontend/components/phase{4,5,6,7a}/**`

## Acceptance Criteria
- [ ] AC-1：TS 类型测试：chart_material 字段加入后 v3.15 既有 TemplateProps 调用方编译不破坏（chart_material 缺省 = undefined）
- [ ] AC-2：单测：构造 `chart_material` + 冲突 `data` → 5 类 chart 模板渲染输出与 chart_material 一致；data 字段被忽略
- [ ] AC-3：property-based 测试（hypothesis-like 在 vitest 中实现）：随机 chart_material → 渲染图表 axis 范围 = chart_material.axis_spec.range
- [ ] AC-4：L1 校验：模板要求 chart 类型但 chart_material 缺失 → 编译期类型错误（discriminated union 或运行期 console.error 二选一，本任务采用运行期 + 单测断言）
- [ ] AC-5：失败样例覆盖：构造冲突场景 → SPEC-22 表中 `chart_material_priority_violation` 类型可识别（前端日志含该字符串）
- [ ] AC-6：v3.15/v3.16 ChartStyleOverrides + 本版 chart_material 联合使用：样式覆盖（color/width）从 ChartStyleOverrides 取，数据/坐标轴从 chart_material 取，两者并存正确

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_013.py -v
npx playwright test tests/integration/frontend/test_chart_render_v317.spec.ts
npx tsc --noEmit src/shared/types/template_props.ts src/frontend/render/chart_material_priority.ts
mypy src/shared/schemas/template_props.py --strict
```

## Completion Definition
TemplateProps 扩展 + 5 类 chart 组件改造 + 优先级模块 + 全部 6 条 AC PASS + ChartStyleOverrides 联合使用回归。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_013.py | template_props_optional_field_compat |
| AC-2 | tests/unit/media-render/test_spec_f_013.py | line_chart_chart_material_overrides_data / bar / pie / candlestick / event_timeline |
| AC-3 | tests/unit/media-render/test_spec_f_013.py | property_based_axis_range_match |
| AC-4 | tests/unit/media-render/test_spec_f_013.py | missing_chart_material_for_chart_type_logs_error |
| AC-5 | tests/unit/media-render/test_spec_f_013.py | log_contains_chart_material_priority_violation |
| AC-6 | tests/unit/media-render/test_spec_f_013.py | chart_style_overrides_and_chart_material_coexist |

## §23.9 验收门禁映射
- 第 8 行：chart_material schema + axis_spec 校验（渲染消费部分）
