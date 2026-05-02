# [SPEC-F-004] EChartsFrameController (Remotion Context)

## Metadata
- **task_id**: SPEC-F-004
- **spec_ref**: SPEC-18.1.3
- **depends_on**: [SPEC-A-001, SPEC-F-001, SPEC-F-002, SPEC-F-003]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Implement `EChartsFrameController` that drives all 8 ECharts templates in Remotion context. Must disable ECharts native animation (`animation: false`), compute `easedProgress` per frame, control data display range via `setOption({ dataZoom })`, and implement pause_trigger freeze/resume logic. Frame mapping: `frame = timeSec * fps`.

## Allowed Files
- `src/frontend/components/templates/echarts/EChartsFrameController.ts`
- `src/frontend/components/templates/echarts/useEChartsFrame.ts`
- `tests/unit/media-render/test_echarts_frame_controller.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: EChartsFrameController initializes with `animation: false`
- [ ] AC-2: Same-frame double render produces identical PNG SHA256
- [ ] AC-3: `pause_trigger` activates when `Math.abs(easedProgress - trigger.at_progress) < 0.01`
- [ ] AC-4: During pause, `onFrame` stops calling `setOption`; ECharts holds current state
- [ ] AC-5: After pause resume, rendering continues from correct position
- [ ] AC-6: Frame formula `frame = timeSec * fps` produces integer frames

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_004.py -v
npx tsc --noEmit
```

## Completion Definition
EChartsFrameController correctly drives chart progression per Remotion frame, freezes on pause_triggers, resumes correctly, and produces deterministic renders. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_004.py | test_animation_disabled_on_init |
| AC-2 | tests/unit/media-render/test_spec_f_004.py | test_deterministic_render_sha256 |
| AC-3 | tests/unit/media-render/test_spec_f_004.py | test_pause_trigger_threshold |
| AC-4 | tests/unit/media-render/test_spec_f_004.py | test_pause_freezes_setoption |
| AC-5 | tests/unit/media-render/test_spec_f_004.py | test_resume_from_correct_position |
| AC-6 | tests/unit/media-render/test_spec_f_004.py | test_frame_formula_integer |
