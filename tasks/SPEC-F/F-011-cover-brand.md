# [SPEC-F-011] Cover Generation, Brand Consistency & Platform Adaptation

## Metadata
- **task_id**: SPEC-F-011
- **spec_ref**: SPEC-21.1, SPEC-21.2, SPEC-22.1, SPEC-22.2
- **depends_on**: [SPEC-A-001, SPEC-F-007]
- **priority**: P1
- **estimated_complexity**: M

## Scope
Implement P11 cover generation: 3 templates (data_focus, chart_preview, clean_text) x 3 aspect ratios (16:9/3:4/1:1) = 9 covers via Pillow. Implement brand_kit inheritance (from SQLite via API, not direct file read): logo/watermark/intro/outro/color_palette/font_family; new projects inherit, project-level override supported. Implement P11 auto-overlay: intro via Remotion Sequence prepend, outro append, watermark+logo via AbsoluteFill. Platform profiles with percentage-based coordinates (no hardcoded pixels). V1 = 16:9 only; douyin → explicit deferral message.

## Allowed Files
- `src/frontend/render/coverGenerator.ts`
- `src/frontend/render/brandKit.ts`
- `src/frontend/render/platformProfile.ts`
- `src/frontend/components/player/BrandOverlay.tsx`
- `tests/unit/media-render/test_cover_brand.test.tsx`

## Forbidden Files
- `src/backend/**`
- `src/shared/types/**` (owned by SPEC-A)

## Acceptance Criteria
- [ ] AC-1: 9 cover files generated (3 templates x 3 ratios)
- [ ] AC-2: 16:9 cover dimensions are 1280x720
- [ ] AC-3: `data_focus` template sources big number from `key_data_point`
- [ ] AC-4: New project theme.json inherits brand_kit values for un-overridden fields
- [ ] AC-5: Project-level `color_palette.primary` override is used in rendering over brand_kit default
- [ ] AC-6: Missing brand_kit falls back to system defaults
- [ ] AC-7: Render layer reads brand_kit from API (`GET /api/settings`), not directly from `brand_kit.json` file
- [ ] AC-8: Intro duration matches `brand_kit.intro_template.duration` within ±0.1s
- [ ] AC-9: All frames contain watermark when `watermark.opacity > 0`
- [ ] AC-10: `watermark.opacity=0` → watermark not rendered
- [ ] AC-11: Remotion Composition width/height read from platform profile
- [ ] AC-12: Subtitles contain no hardcoded pixel values
- [ ] AC-13: `target_platform=douyin` → explicit deferral message returned

## Verification Commands
```bash
pytest tests/unit/media-render/test_spec_f_011.py -v
npx tsc --noEmit
```

## Completion Definition
Cover generator produces 9 files at correct dimensions, brand_kit is inherited/overridden correctly from API, intro/outro/watermark overlay works, platform profiles use percentage coordinates, and all tests pass.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/media-render/test_spec_f_011.py | test_nine_covers_generated |
| AC-2 | tests/unit/media-render/test_spec_f_011.py | test_16_9_dimensions |
| AC-3 | tests/unit/media-render/test_spec_f_011.py | test_data_focus_key_data_point |
| AC-4 | tests/unit/media-render/test_spec_f_011.py | test_brand_kit_inheritance |
| AC-5 | tests/unit/media-render/test_spec_f_011.py | test_project_override_color |
| AC-6 | tests/unit/media-render/test_spec_f_011.py | test_missing_brand_kit_defaults |
| AC-7 | tests/unit/media-render/test_spec_f_011.py | test_brand_kit_from_api |
| AC-8 | tests/unit/media-render/test_spec_f_011.py | test_intro_duration_match |
| AC-9 | tests/unit/media-render/test_spec_f_011.py | test_watermark_all_frames |
| AC-10 | tests/unit/media-render/test_spec_f_011.py | test_watermark_opacity_zero_hidden |
| AC-11 | tests/unit/media-render/test_spec_f_011.py | test_composition_from_platform_profile |
| AC-12 | tests/unit/media-render/test_spec_f_011.py | test_no_hardcoded_pixels_in_subtitles |
| AC-13 | tests/unit/media-render/test_spec_f_011.py | test_douyin_deferral |
