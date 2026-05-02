# [SPEC-A-004] Cross-Module Shared Type Definitions

## Metadata
- **task_id**: SPEC-A-004
- **spec_ref**: SPEC-0A.6, SPEC-0A.7
- **depends_on**: [SPEC-A-001]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Define all cross-module shared types from SPEC-0A.7: KeyDataPoint, VoiceParams, SegmentVoiceOverrides, SubtitleWord, DiscreteKeyframe, ContinuousKeyframe, ThemeConfig, TemplateProps. Also define the style_lock state ownership rules from SPEC-0A.6 as code documentation/constants.

## Allowed Files
- `src/shared/types/shared_types.ts`
- `src/shared/schemas/shared_types.py`
- `src/shared/types/template_props.ts`
- `src/shared/schemas/template_props.py`
- `tests/unit/contracts/test_shared_types.py`

## Forbidden Files
- `src/backend/api/**`
- `src/backend/engine/**`
- `src/frontend/components/**`

## Acceptance Criteria
- [ ] AC-1: `KeyDataPoint` type has all 7 fields including data_point_id (dp_ prefix), trust_level enum (3 values), segment_id
- [ ] AC-2: `VoiceParams` type has voice_id, style, style_degree [0.01, 2.0], rate_wpm, pitch, volume
- [ ] AC-3: `SegmentVoiceOverrides` type has rate_multiplier [0.8, 1.2], emotion, style_degree, emphasis_words[], volume
- [ ] AC-4: `SubtitleWord` type has word, start_sec, end_sec, highlight_type (4 values + null)
- [ ] AC-5: `DiscreteKeyframe` has type='discrete', time_offset_sec, action enum (6 values), target, optional annotation
- [ ] AC-6: `ContinuousKeyframe` has type='continuous', start_sec, end_sec, easing enum (4 values), progress_mapping[], optional pause_triggers[]
- [ ] AC-7: `ThemeConfig` has color_palette[], background_color, font_family, chart_style (4 sub-fields), subtitle_style
- [ ] AC-8: `TemplateProps` has templateId, data, annotationKeyframes (union of Discrete|Continuous), timelineSegment, theme, fps
- [ ] AC-9: style_lock ownership documented: write via StoryboardAgent, read by KeyframeRenderAgent and ThemeConfig

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_004.py -v
mypy src/shared/schemas/shared_types.py src/shared/schemas/template_props.py --strict
npx tsc --noEmit src/shared/types/shared_types.ts src/shared/types/template_props.ts
```

## Completion Definition
All 8 shared types defined in both TS and Python with full field validation. Range constraints (style_degree, rate_multiplier) enforced by validators. TS and Python definitions match. Tests cover valid payloads, boundary values, and invalid enum values.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_004.py | test_key_data_point_valid |
| AC-1 | tests/unit/contracts/test_spec_a_004.py | test_key_data_point_id_prefix |
| AC-2 | tests/unit/contracts/test_spec_a_004.py | test_voice_params_style_degree_range |
| AC-3 | tests/unit/contracts/test_spec_a_004.py | test_segment_voice_overrides_rate_range |
| AC-4 | tests/unit/contracts/test_spec_a_004.py | test_subtitle_word_highlight_type_enum |
| AC-5 | tests/unit/contracts/test_spec_a_004.py | test_discrete_keyframe_action_enum |
| AC-6 | tests/unit/contracts/test_spec_a_004.py | test_continuous_keyframe_easing_enum |
| AC-6 | tests/unit/contracts/test_spec_a_004.py | test_continuous_keyframe_pause_triggers |
| AC-7 | tests/unit/contracts/test_spec_a_004.py | test_theme_config_structure |
| AC-8 | tests/unit/contracts/test_spec_a_004.py | test_template_props_union_keyframes |
| AC-9 | tests/unit/contracts/test_spec_a_004.py | test_style_lock_ownership_constants |
