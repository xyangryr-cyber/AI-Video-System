# [SPEC-E-005] Phase Artifact Preview Components (P0-P11)

## Metadata
- **task_id**: SPEC-E-005
- **spec_ref**: SPEC-2.6
- **depends_on**: [SPEC-A-001, SPEC-E-003]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement 12 phase-specific preview components for the workflow page center area. Each component receives props matching the contract defined in SPEC-2.6 table. Components: P0 structured form view, P1/P3 rich text, P2 collapsible segment view, P4 segmented audio player (per-segment play/pause), P5 waveform + player, P6 trigger-point list player, P7 storyboard card gallery, P8 grid gallery with click-to-zoom, P9 thumbnail gallery, P10 embedded video player, P11 embedded player + covers + download button. A PhasePreviewRouter dispatches to the correct component based on current phase.

## Allowed Files
- `src/frontend/components/previews/PhasePreviewRouter.tsx`
- `src/frontend/components/previews/P0RequirementsView.tsx`
- `src/frontend/components/previews/P1ScriptView.tsx`
- `src/frontend/components/previews/P2SegmentView.tsx`
- `src/frontend/components/previews/P3VoiceScriptView.tsx`
- `src/frontend/components/previews/P4SegmentAudioPlayer.tsx`
- `src/frontend/components/previews/P5WaveformPlayer.tsx`
- `src/frontend/components/previews/P6SfxListPlayer.tsx`
- `src/frontend/components/previews/P7StoryboardGallery.tsx`
- `src/frontend/components/previews/P8FrameGallery.tsx`
- `src/frontend/components/previews/P9BrollGallery.tsx`
- `src/frontend/components/previews/P10VideoPlayer.tsx`
- `src/frontend/components/previews/P11FinalPlayer.tsx`
- `src/frontend/types/preview.ts`
- `tests/unit/frontend/previews/PhasePreviewRouter.test.tsx`
- `tests/unit/frontend/previews/P4SegmentAudioPlayer.test.tsx`
- `tests/unit/frontend/previews/P8FrameGallery.test.tsx`
- `tests/unit/frontend/previews/P11FinalPlayer.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: PhasePreviewRouter renders the correct component for each of 12 phases (P0-P11)
- [ ] AC-2: Each component accepts and renders props matching SPEC-2.6 contract table
- [ ] AC-3: P4 segmented audio player supports per-segment play/pause controls
- [ ] AC-4: P8 grid gallery supports click-to-zoom (modal or lightbox overlay)
- [ ] AC-5: P11 renders embedded player + cover images + functional download button
- [ ] AC-6: Components handle empty/missing data gracefully (empty state, not crash)

## Verification Commands
```bash
pytest tests/unit/frontend/test_spec_e_005.py -v
tsc --noEmit
```

## Completion Definition
All 12 preview components render correctly for their respective phase data. Router dispatches to the right component. P4 play/pause, P8 zoom, P11 download all functional. All tests pass, no type errors.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/frontend/test_spec_e_005.py | test_routes_to_correct_component_for_each_phase |
| AC-2 | tests/unit/frontend/test_spec_e_005.py | test_components_accept_spec_props |
| AC-3 | tests/unit/frontend/test_spec_e_005.py | test_per_segment_play_pause |
| AC-4 | tests/unit/frontend/test_spec_e_005.py | test_click_to_zoom |
| AC-5 | tests/unit/frontend/test_spec_e_005.py | test_player_covers_download |
| AC-6 | tests/unit/frontend/test_spec_e_005.py | test_empty_data_graceful |
