# [SPEC-F-003] ECharts Templates: Candlestick, Comparison Chart

## Metadata
- **task_id**: SPEC-F-003
- **spec_ref**: SPEC-18.1.1
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement 2 ECharts chart templates: `candlestick_chart` and `comparison_chart`. Each must implement `React.FC<TemplateProps>`, use ECharts-native animation for non-Remotion preview, and support `annotation_keyframes`. Register both in `template_registry.ts`.

## Allowed Files
- `src/frontend/components/templates/echarts/CandlestickChart.tsx`
- `src/frontend/components/templates/echarts/ComparisonChart.tsx`
- `src/frontend/components/templates/template_registry.ts`
- `tests/unit/media-render/test_echarts_candlestick_comparison.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: `candlestick_chart` contains `candlestick` + `line` (MA lines) + `bar` (volume) three series types
- [ ] AC-2: `candlestick_chart` uses `dataZoom` for zoom control + `animationDelay` for sequential candle draw
- [ ] AC-3: `comparison_chart` uses multiple `line`/`bar` series sharing `xAxis` + `markArea` + `markLine` for divergence highlight
- [ ] AC-4: Both templates implement `React.FC<TemplateProps>` interface
- [ ] AC-5: Both templates registered in `template_registry.ts`

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_003.py -v
npx tsc --noEmit
```

## Completion Definition
Both ECharts components render correctly with sample data, are registered in template_registry, accept TemplateProps, and all tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_003.py | test_candlestick_three_series |
| AC-2 | tests/unit/media-render/test_spec_f_003.py | test_candlestick_datazoom_and_delay |
| AC-3 | tests/unit/media-render/test_spec_f_003.py | test_comparison_shared_axis_and_divergence |
| AC-4 | tests/unit/media-render/test_spec_f_003.py | test_all_implement_template_props |
| AC-5 | tests/unit/media-render/test_spec_f_003.py | test_all_registered_in_registry |
