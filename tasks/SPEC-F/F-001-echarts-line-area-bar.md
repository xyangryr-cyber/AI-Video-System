# [SPEC-F-001] ECharts Templates: Line, Area, Bar Charts

## Metadata
- **task_id**: SPEC-F-001
- **spec_ref**: SPEC-18.1.1
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement 3 ECharts chart templates: `animated_line_chart`, `animated_area_chart`, `animated_bar_chart`. Each must implement `React.FC<TemplateProps>` (SPEC-A SPEC-0A.7), use ECharts-native animation config for non-Remotion preview, and support `annotation_keyframes`. Register all 3 in `template_registry.ts`.

## Allowed Files
- `src/frontend/components/templates/echarts/AnimatedLineChart.tsx`
- `src/frontend/components/templates/echarts/AnimatedAreaChart.tsx`
- `src/frontend/components/templates/echarts/AnimatedBarChart.tsx`
- `src/frontend/components/templates/template_registry.ts`
- `tests/unit/media-render/test_echarts_line_area_bar.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `animated_line_chart` uses `markPoint` for highlight + `graphic` component for arrow following
- [ ] AC-2: `animated_line_chart` uses `animationDuration` + `animationDelay` for point-by-point draw in non-Remotion preview
- [ ] AC-3: `animated_area_chart` uses `areaStyle` + `animationDuration` for fill animation and `visualMap` for gradient colors
- [ ] AC-4: `animated_bar_chart` uses `animationDelay` by `dataIndex` ascending for sequential growth + `emphasis` state for highlight color change
- [ ] AC-5: All 3 templates implement `React.FC<TemplateProps>` interface
- [ ] AC-6: All 3 templates registered in `template_registry.ts` under correct template IDs
- [ ] AC-7: All 3 templates accept `annotation_keyframes` parameter

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_001.py -v
npx tsc --noEmit
```

## Completion Definition
Three ECharts chart components render correctly with sample data, are registered in template_registry, accept TemplateProps, and all tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_001.py | test_line_chart_markpoint_highlight |
| AC-2 | tests/unit/media-render/test_spec_f_001.py | test_line_chart_native_animation_config |
| AC-3 | tests/unit/media-render/test_spec_f_001.py | test_area_chart_fill_and_gradient |
| AC-4 | tests/unit/media-render/test_spec_f_001.py | test_bar_chart_sequential_growth |
| AC-5 | tests/unit/media-render/test_spec_f_001.py | test_all_implement_template_props |
| AC-6 | tests/unit/media-render/test_spec_f_001.py | test_all_registered_in_registry |
| AC-7 | tests/unit/media-render/test_spec_f_001.py | test_all_accept_annotation_keyframes |
