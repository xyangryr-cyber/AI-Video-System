# [SPEC-F-102] 预览态 vs 生产态渲染

## Metadata
- **task_id**: SPEC-F-102
- **spec_ref**: SPEC-F §F-BDD-3
- **depends_on**: [SPEC-A-103]
- **priority**: P0
- **estimated_complexity**: L

## Scope
扩展 Remotion composition 支持 preview / production 两种渲染模式，共享同一份 data / axis_spec / style_overrides，且模式切换不触发后端数据重跑。

## Allowed Files
- `src/frontend/remotion/compositions/PreviewComposition.tsx`
- `src/frontend/remotion/compositions/ProductionComposition.tsx`
- `src/frontend/remotion/utils/render_mode_controller.ts`
- `tests/e2e/render_mode_switch.spec.ts`

## Acceptance Criteria
- [ ] AC-1: mode='preview' 输出 480p,单帧 ≤ 500ms
- [ ] AC-2: mode='production' 输出 1080p,完整动画
- [ ] AC-3: 两态共享 data / axis_spec / style_overrides(不分叉数据)
- [ ] AC-4: 切换 mode 不触发后端数据重跑

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_102.py -v
npx playwright test tests/e2e/render_mode_switch.spec.ts
```

## Completion Definition
PreviewComposition 与 ProductionComposition 通过 render_mode_controller 共享同一数据源，预览态在 480p 下达成 ≤ 500ms 单帧渲染，生产态输出 1080p 完整动画，且模式切换在前端完成、不触发后端数据重跑。

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_102.py | test_preview_mode_480p_frame_under_500ms |
| AC-2 | tests/unit/media-render/test_spec_f_102.py | test_production_mode_1080p_full_animation |
| AC-3 | tests/unit/media-render/test_spec_f_102.py | test_shared_data_axis_style_no_fork |
| AC-4 | tests/unit/media-render/test_spec_f_102.py | test_mode_switch_no_backend_rerun |
