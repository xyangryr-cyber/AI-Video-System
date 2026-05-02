# [SPEC-F-100] ChartStyleOverrides 渲染规格

## Metadata
- **task_id**: SPEC-F-100
- **spec_ref**: SPEC-F §F-BDD-1
- **depends_on**: [SPEC-A-103]
- **priority**: P0
- **estimated_complexity**: M

## Scope
在 ChartTemplate 渲染管线中支持 ChartStyleOverrides 输入，按照 overrides > theme_config > template default 的优先级合并样式，并保持与 v3.15 TemplateProps 的向后兼容。

## Allowed Files
- `src/frontend/remotion/components/ChartTemplate.tsx`
- `src/frontend/remotion/utils/chart_style_merger.ts`
- `tests/unit/remotion/test_chart_style_priority.ts`

## Acceptance Criteria
- [ ] AC-1: 优先级 ChartStyleOverrides > theme_config > template default
- [ ] AC-2: 颜色不在 palette 内 → fallback 至 palette[0] + 结构化日志
- [ ] AC-3: show_source_label 仅在 verified 时显示
- [ ] AC-4: 与 v3.15 TemplateProps 向后兼容

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_100.py -v
```

## Completion Definition
ChartTemplate 接受 ChartStyleOverrides 并按规定优先级合并样式，非法颜色降级且记录结构化日志，source_label 受 verified 控制，旧版 TemplateProps 调用方无需修改即可继续工作。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_100.py | test_overrides_beats_theme_and_default |
| AC-2 | tests/unit/media-render/test_spec_f_100.py | test_invalid_color_fallback_to_palette_zero |
| AC-3 | tests/unit/media-render/test_spec_f_100.py | test_show_source_label_only_when_verified |
| AC-4 | tests/unit/media-render/test_spec_f_100.py | test_backward_compat_v315_template_props |
