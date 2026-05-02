# [SPEC-F-007] Remotion Orchestration Layer & Template Registry

## Metadata
- **task_id**: SPEC-F-007
- **spec_ref**: SPEC-18.3
- **depends_on**: [SPEC-A-001, SPEC-F-001, SPEC-F-002, SPEC-F-003, SPEC-F-005, SPEC-F-006]
- **priority**: P0
- **estimated_complexity**: L

## Scope
Implement Layer 3 Remotion orchestration: `<Composition>` for fps/resolution/duration, `<Sequence>` for timeline.json-driven segment scheduling, `useCurrentFrame()` + `interpolate()` driving Layer 1/2 components, `<AbsoluteFill>` for layer stacking (background/chart/annotation/subtitle), `TEMPLATE_MAPPING` covering all 15 templates, and `renderMedia()` server-side render pipeline. Layer 3 code must NOT import animation libraries (framer-motion, gsap, etc.).

## Allowed Files
- `src/frontend/components/player/VideoComposition.tsx`
- `src/frontend/components/player/SegmentSequencer.tsx`
- `src/frontend/components/player/LayerStack.tsx`
- `src/frontend/components/templates/template_registry.ts`
- `src/frontend/render/renderPipeline.ts`
- `tests/unit/media-render/test_remotion_orchestration.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: Layer 3 code has zero imports of `framer-motion`, `gsap`, or other animation libraries
- [ ] AC-2: `TEMPLATE_MAPPING` covers all 15 templates (8 ECharts + 7 React community) matching the data_type→template_id table
- [ ] AC-3: `TEMPLATE_MAPPING` lookup returns `null`/`undefined` only when data_type has no mapping; LLM recommendation is invoked only in that case
- [ ] AC-4: All `annotation_keyframes` are validated against `timeline.json` alignment (programmatic check)
- [ ] AC-5: All numeric params (`data_points`, `ohlc_data`) traceable via `data_point_id` to P2 `key_data_point`
- [ ] AC-6: Continuous keyframe `pause_triggers` correctly freeze frames via `useCurrentFrame()`
- [ ] AC-7: `<Composition>` reads fps/width/height from platform profile config

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_007.py -v
npx tsc --noEmit
grep -rE "from ['\"]framer-motion|from ['\"]gsap" src/frontend/components/player/ src/frontend/render/ && exit 1 || echo "OK: no animation lib in Layer 3"
```

## Completion Definition
Remotion orchestration layer sequences all 15 templates by timeline.json, validates keyframe alignment, contains no animation library imports, and all tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_007.py | test_no_animation_lib_imports |
| AC-2 | tests/unit/media-render/test_spec_f_007.py | test_template_mapping_covers_15 |
| AC-3 | tests/unit/media-render/test_spec_f_007.py | test_template_mapping_fallback_to_llm |
| AC-4 | tests/unit/media-render/test_spec_f_007.py | test_keyframe_timeline_alignment |
| AC-5 | tests/unit/media-render/test_spec_f_007.py | test_data_point_id_traceability |
| AC-6 | tests/unit/media-render/test_spec_f_007.py | test_pause_trigger_frame_freeze |
| AC-7 | tests/unit/media-render/test_spec_f_007.py | test_composition_reads_platform_profile |
