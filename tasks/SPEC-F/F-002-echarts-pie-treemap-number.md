# [SPEC-F-002] ECharts Templates: Pie, Treemap, Number Callout

## Metadata
- **task_id**: SPEC-F-002
- **spec_ref**: SPEC-18.1.1
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement 3 ECharts chart templates: `animated_pie_chart`, `treemap_chart`, `number_callout`. Each must implement `React.FC<TemplateProps>`, use ECharts-native animation for non-Remotion preview, and support `annotation_keyframes`. Register all 3 in `template_registry.ts`.

## Allowed Files
- `src/frontend/components/templates/echarts/AnimatedPieChart.tsx`
- `src/frontend/components/templates/echarts/TreemapChart.tsx`
- `src/frontend/components/templates/echarts/NumberCallout.tsx`
- `src/frontend/components/templates/template_registry.ts`
- `tests/unit/media-render/test_echarts_pie_treemap_number.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `animated_pie_chart` uses `startAngle` + `animationDuration` for rotational reveal + `selectedMode` for sector explode
- [ ] AC-2: `treemap_chart` uses treemap series native `drillDown` + `animationDurationUpdate` for hierarchical expand
- [ ] AC-3: `number_callout` uses `graphic` component for count-up animation + CSS `@keyframes` for pulse-scale effect
- [ ] AC-4: All 3 templates implement `React.FC<TemplateProps>` interface
- [ ] AC-5: All 3 templates registered in `template_registry.ts` under correct template IDs
- [ ] AC-6: `number_callout` accepts `number, unit, count_up_duration, emphasis_color, comparison{}` params

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_002.py -v
npx tsc --noEmit
```

## Completion Definition
Three ECharts components render correctly with sample data, are registered in template_registry, accept TemplateProps, and all tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_002.py | test_pie_chart_rotational_reveal_and_explode |
| AC-2 | tests/unit/media-render/test_spec_f_002.py | test_treemap_drill_down_animation |
| AC-3 | tests/unit/media-render/test_spec_f_002.py | test_number_callout_countup_and_pulse |
| AC-4 | tests/unit/media-render/test_spec_f_002.py | test_all_implement_template_props |
| AC-5 | tests/unit/media-render/test_spec_f_002.py | test_all_registered_in_registry |
| AC-6 | tests/unit/media-render/test_spec_f_002.py | test_number_callout_params |
