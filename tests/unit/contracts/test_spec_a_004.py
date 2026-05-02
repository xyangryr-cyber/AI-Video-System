"""Tests for [SPEC-A-004] Cross-Module Shared Type Definitions."""

from __future__ import annotations

from tests.unit.contracts import test_shared_types as ref


class TestAC1KeyDataPoint:
    def test_key_data_point_valid(self):
        ref.test_key_data_point_valid()

    def test_key_data_point_id_prefix(self):
        ref.test_key_data_point_id_prefix()


class TestAC2VoiceParams:
    def test_voice_params_style_degree_range(self):
        ref.test_voice_params_style_degree_range()


class TestAC3SegmentVoiceOverrides:
    def test_segment_voice_overrides_rate_range(self):
        ref.test_segment_voice_overrides_rate_range()


class TestAC4SubtitleWord:
    def test_subtitle_word_highlight_type_enum(self):
        ref.test_subtitle_word_highlight_type_enum()


class TestAC5DiscreteKeyframe:
    def test_discrete_keyframe_action_enum(self):
        ref.test_discrete_keyframe_action_enum()


class TestAC6ContinuousKeyframe:
    def test_continuous_keyframe_easing_enum(self):
        ref.test_continuous_keyframe_easing_enum()

    def test_continuous_keyframe_pause_triggers(self):
        ref.test_continuous_keyframe_pause_triggers()


class TestAC7ThemeConfig:
    def test_theme_config_structure(self):
        ref.test_theme_config_structure()


class TestAC8TemplateProps:
    def test_template_props_union_keyframes(self):
        ref.test_template_props_union_keyframes()


class TestAC9StyleLockOwnershipDocumented:
    def test_style_lock_ownership_constants(self):
        ref.test_style_lock_ownership_constants()
