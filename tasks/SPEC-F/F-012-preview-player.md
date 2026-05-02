# [SPEC-F-012] Preview Player & Layer Decomposition

## Metadata
- **task_id**: SPEC-F-012
- **spec_ref**: SPEC-23.1, SPEC-23.2
- **depends_on**: [SPEC-A-001, SPEC-F-007, SPEC-F-010]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement preview player using `@remotion/player`: frame-level stepping (arrow keys ±1 frame, Shift+arrow ±10 frames), playback speed (0.5x/1x/1.5x/2x), JKL shuttle control, timeline annotation (M key → user_annotation entry in task_ledger), and 4-layer decomposition preview (text/data/visual/audio toggles). Layer toggle must only trigger the corresponding Producer for re-render, not full regeneration.

## Allowed Files
- `src/frontend/components/player/PreviewPlayer.tsx`
- `src/frontend/components/player/LayerToggle.tsx`
- `src/frontend/components/player/KeyboardControls.ts`
- `src/frontend/components/player/TimelineAnnotation.tsx`
- `tests/unit/media-render/test_preview_player.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Right arrow key increments `currentFrame` by 1
- [ ] AC-2: Shift+Right arrow increments `currentFrame` by 10
- [ ] AC-3: M key followed by text input creates `task_ledger` entry with `task_type=user_annotation, params={frame, time_sec, text}`
- [ ] AC-4: `visibleLayers` toggle causes each layer to respond immediately
- [ ] AC-5: Layer toggle buttons show 4 toggles: text, data, visual, audio
- [ ] AC-6: Viewing data layer alone renders only charts/info cards (no text, no background, no audio waveform)
- [ ] AC-7: Layer-specific feedback routes to corresponding Producer only, no full regeneration

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_012.py -v
npx tsc --noEmit
```

## Completion Definition
Preview player supports all keyboard shortcuts, speed controls, timeline annotations, and 4-layer decomposition with selective Producer routing. All tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_012.py | test_arrow_key_frame_step |
| AC-2 | tests/unit/media-render/test_spec_f_012.py | test_shift_arrow_ten_frame_step |
| AC-3 | tests/unit/media-render/test_spec_f_012.py | test_m_key_annotation_to_task_ledger |
| AC-4 | tests/unit/media-render/test_spec_f_012.py | test_visible_layers_immediate_response |
| AC-5 | tests/unit/media-render/test_spec_f_012.py | test_four_layer_toggles |
| AC-6 | tests/unit/media-render/test_spec_f_012.py | test_data_layer_isolation |
| AC-7 | tests/unit/media-render/test_spec_f_012.py | test_layer_feedback_selective_producer |
