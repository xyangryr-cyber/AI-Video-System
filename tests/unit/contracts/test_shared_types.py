"""Tests for [SPEC-A-004] Cross-Module Shared Type Definitions.

Covers AC-1..AC-9 from tasks/SPEC-A/A-004-shared-types.md against
SPEC-0A.6 (style_lock ownership) and SPEC-0A.7 (cross-module shared types).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

from src.shared.schemas.shared_types import (
    CONTINUOUS_EASING_VALUES,
    DISCRETE_ACTION_VALUES,
    HIGHLIGHT_TYPE_VALUES,
    STYLE_LOCK_OWNERSHIP,
    TRUST_LEVEL_VALUES,
    ContinuousKeyframe,
    DiscreteKeyframe,
    KeyDataPoint,
    ProgressMapping,
    SegmentVoiceOverrides,
    SubtitleWord,
    ThemeConfig,
    ThemeChartStyle,
    VoiceParams,
)
from src.shared.schemas.template_props import TemplateProps, TimelineSegmentRange

ROOT = Path(__file__).resolve().parents[3]
TS_SHARED = ROOT / "src" / "shared" / "types" / "shared_types.ts"
TS_TEMPLATE = ROOT / "src" / "shared" / "types" / "template_props.ts"


def _valid_key_data_point(**overrides) -> dict:
    base = {
        "data_point_id": "dp_001",
        "label": "黄金价格",
        "value": "3421.5",
        "unit": "USD/oz",
        "source": "https://example.com/source",
        "trust_level": "user_verified",
        "segment_id": "seg_03",
    }
    base.update(overrides)
    return base


def _valid_voice_params(**overrides) -> dict:
    base = {
        "voice_id": "zh-CN-XiaoxiaoNeural",
        "style": "cheerful",
        "style_degree": 1.0,
        "rate_wpm": 280.0,
        "pitch": 0.0,
        "volume": 1.0,
    }
    base.update(overrides)
    return base


def _valid_segment_overrides(**overrides) -> dict:
    base = {
        "rate_multiplier": 1.0,
        "emotion": "neutral",
        "style_degree": 1.2,
        "emphasis_words": ["黄金", "价格"],
        "volume": 5.0,
    }
    base.update(overrides)
    return base


def _valid_subtitle_word(**overrides) -> dict:
    base = {
        "word": "黄金",
        "start_sec": 0.0,
        "end_sec": 0.5,
        "highlight_type": "key_data",
    }
    base.update(overrides)
    return base


def _valid_discrete_keyframe(**overrides) -> dict:
    base = {
        "type": "discrete",
        "time_offset_sec": 1.5,
        "action": "highlight",
        "target": "bar_3",
        "annotation": "峰值",
    }
    base.update(overrides)
    return base


def _valid_continuous_keyframe(**overrides) -> dict:
    base = {
        "type": "continuous",
        "start_sec": 0.0,
        "end_sec": 4.0,
        "easing": "ease_in_out",
        "progress_mapping": [
            {"progress": 0.0, "data_index": 0, "label": "start"},
            {"progress": 1.0, "data_index": 5},
        ],
    }
    base.update(overrides)
    return base


def _valid_theme_config(**overrides) -> dict:
    base = {
        "color_palette": ["#1a73e8", "#34a853", "#ea4335"],
        "background_color": "#ffffff",
        "font_family": "Noto Sans SC",
        "chart_style": {
            "axis_color": "#666",
            "grid_color": "#eee",
            "label_font_size": 14,
            "tooltip_style": {"border_radius": 4},
        },
        "subtitle_style": {"font_weight": "bold"},
    }
    base.update(overrides)
    return base


def _valid_template_props(**overrides) -> dict:
    base = {
        "templateId": "line_chart_v1",
        "data": {"rows": [1, 2, 3]},
        "annotationKeyframes": [
            _valid_discrete_keyframe(),
            _valid_continuous_keyframe(),
        ],
        "timelineSegment": {"startFrame": 0, "endFrame": 120},
        "theme": _valid_theme_config(),
        "fps": 30,
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# AC-1: KeyDataPoint
# ---------------------------------------------------------------------------
def test_key_data_point_valid():
    expected = {
        "data_point_id",
        "label",
        "value",
        "unit",
        "source",
        "trust_level",
        "segment_id",
        "usage",
        "link",
    }
    assert set(KeyDataPoint.model_fields.keys()) == expected
    KeyDataPoint.model_validate(_valid_key_data_point())
    # value accepts string or number per SPEC-0A.7
    KeyDataPoint.model_validate(_valid_key_data_point(value=3421.5))
    KeyDataPoint.model_validate(_valid_key_data_point(value=100))

    assert set(TRUST_LEVEL_VALUES) == {
        "user_verified",
        "source_verified",
        "llm_generated",
    }
    for level in TRUST_LEVEL_VALUES:
        KeyDataPoint.model_validate(_valid_key_data_point(trust_level=level))
    with pytest.raises(ValidationError):
        KeyDataPoint.model_validate(_valid_key_data_point(trust_level="unknown"))

    ts = TS_SHARED.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+KeyDataPoint\b", ts)
    for field in expected:
        assert re.search(rf"\b{field}\b", ts), f"shared_types.ts missing: {field}"


def test_key_data_point_id_prefix():
    KeyDataPoint.model_validate(_valid_key_data_point(data_point_id="dp_042"))
    for bad in ("datapoint_1", "dp", "xp_001", "dp-001"):
        with pytest.raises(ValidationError):
            KeyDataPoint.model_validate(_valid_key_data_point(data_point_id=bad))


# ---------------------------------------------------------------------------
# AC-2: VoiceParams
# ---------------------------------------------------------------------------
def test_voice_params_style_degree_range():
    expected = {"voice_id", "style", "style_degree", "rate_wpm", "pitch", "volume"}
    assert set(VoiceParams.model_fields.keys()) == expected

    # boundary values allowed
    VoiceParams.model_validate(_valid_voice_params(style_degree=0.01))
    VoiceParams.model_validate(_valid_voice_params(style_degree=2.0))

    # out of range rejected
    for bad in (0.0, 0.009, 2.001, -0.5, 3.0):
        with pytest.raises(ValidationError):
            VoiceParams.model_validate(_valid_voice_params(style_degree=bad))

    ts = TS_SHARED.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+VoiceParams\b", ts)
    for field in expected:
        assert re.search(rf"\b{field}\b", ts)


# ---------------------------------------------------------------------------
# AC-3: SegmentVoiceOverrides
# ---------------------------------------------------------------------------
def test_segment_voice_overrides_rate_range():
    expected = {
        "rate_multiplier",
        "emotion",
        "style_degree",
        "emphasis_words",
        "volume",
    }
    assert set(SegmentVoiceOverrides.model_fields.keys()) == expected

    SegmentVoiceOverrides.model_validate(_valid_segment_overrides(rate_multiplier=0.8))
    SegmentVoiceOverrides.model_validate(_valid_segment_overrides(rate_multiplier=1.2))

    for bad in (0.79, 1.21, 0.5, 1.5):
        with pytest.raises(ValidationError):
            SegmentVoiceOverrides.model_validate(
                _valid_segment_overrides(rate_multiplier=bad)
            )

    ts = TS_SHARED.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+SegmentVoiceOverrides\b", ts)
    for field in expected:
        assert re.search(rf"\b{field}\b", ts)


# ---------------------------------------------------------------------------
# AC-4: SubtitleWord highlight_type enum (4 values + null)
# ---------------------------------------------------------------------------
def test_subtitle_word_highlight_type_enum():
    expected = {"word", "start_sec", "end_sec", "highlight_type"}
    assert set(SubtitleWord.model_fields.keys()) == expected

    assert set(HIGHLIGHT_TYPE_VALUES) == {
        "key_data",
        "percentage",
        "number",
        "proper_noun",
        None,
    }
    for value in HIGHLIGHT_TYPE_VALUES:
        SubtitleWord.model_validate(_valid_subtitle_word(highlight_type=value))
    with pytest.raises(ValidationError):
        SubtitleWord.model_validate(_valid_subtitle_word(highlight_type="emphasis"))

    ts = TS_SHARED.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+SubtitleWord\b", ts)
    for token in ("key_data", "percentage", "number", "proper_noun", "null"):
        assert token in ts, f"shared_types.ts missing highlight literal: {token}"


# ---------------------------------------------------------------------------
# AC-5: DiscreteKeyframe action enum (6 values)
# ---------------------------------------------------------------------------
def test_discrete_keyframe_action_enum():
    expected = {"type", "time_offset_sec", "action", "target", "annotation"}
    assert set(DiscreteKeyframe.model_fields.keys()) == expected

    assert set(DISCRETE_ACTION_VALUES) == {
        "highlight",
        "zoom_in",
        "zoom_out",
        "annotate",
        "dim",
        "reset",
    }
    for action in DISCRETE_ACTION_VALUES:
        DiscreteKeyframe.model_validate(_valid_discrete_keyframe(action=action))
    with pytest.raises(ValidationError):
        DiscreteKeyframe.model_validate(_valid_discrete_keyframe(action="shake"))

    # annotation is optional
    payload = _valid_discrete_keyframe()
    payload.pop("annotation")
    DiscreteKeyframe.model_validate(payload)

    # type literal enforced
    with pytest.raises(ValidationError):
        DiscreteKeyframe.model_validate(_valid_discrete_keyframe(type="continuous"))

    ts = TS_SHARED.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+DiscreteKeyframe\b", ts)
    for token in DISCRETE_ACTION_VALUES:
        assert token in ts


# ---------------------------------------------------------------------------
# AC-6: ContinuousKeyframe easing enum (4 values) + optional pause_triggers
# ---------------------------------------------------------------------------
def test_continuous_keyframe_easing_enum():
    expected = {
        "type",
        "start_sec",
        "end_sec",
        "easing",
        "progress_mapping",
        "pause_triggers",
    }
    assert set(ContinuousKeyframe.model_fields.keys()) == expected

    assert set(CONTINUOUS_EASING_VALUES) == {
        "linear",
        "ease_in",
        "ease_out",
        "ease_in_out",
    }
    for easing in CONTINUOUS_EASING_VALUES:
        ContinuousKeyframe.model_validate(_valid_continuous_keyframe(easing=easing))
    with pytest.raises(ValidationError):
        ContinuousKeyframe.model_validate(_valid_continuous_keyframe(easing="bounce"))

    # type literal enforced
    with pytest.raises(ValidationError):
        ContinuousKeyframe.model_validate(_valid_continuous_keyframe(type="discrete"))

    # progress_mapping label optional; progress/data_index required
    mapping_ok = [{"progress": 0.5, "data_index": 2}]
    ContinuousKeyframe.model_validate(
        _valid_continuous_keyframe(progress_mapping=mapping_ok)
    )
    with pytest.raises(ValidationError):
        ContinuousKeyframe.model_validate(
            _valid_continuous_keyframe(progress_mapping=[{"progress": 0.5}])
        )

    # ProgressMapping class surfaced directly
    ProgressMapping.model_validate({"progress": 0.0, "data_index": 0})

    ts = TS_SHARED.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+ContinuousKeyframe\b", ts)
    for token in CONTINUOUS_EASING_VALUES:
        assert token in ts


def test_continuous_keyframe_pause_triggers():
    payload = _valid_continuous_keyframe()
    # pause_triggers is optional
    payload.pop("pause_triggers", None)
    ContinuousKeyframe.model_validate(payload)

    payload_with_trigger = _valid_continuous_keyframe(
        pause_triggers=[
            {
                "at_progress": 0.5,
                "duration_sec": 1.0,
                "narration_keyword": "注意",
                "action": "highlight",
                "target_data_range": [2, 5],
            }
        ]
    )
    model = ContinuousKeyframe.model_validate(payload_with_trigger)
    assert model.pause_triggers is not None
    assert len(model.pause_triggers) == 1
    assert model.pause_triggers[0].at_progress == 0.5

    # target_data_range is optional (tuple[int,int] when present)
    payload_no_range = _valid_continuous_keyframe(
        pause_triggers=[
            {
                "at_progress": 0.8,
                "duration_sec": 0.3,
                "narration_keyword": "然后",
                "action": "dim",
            }
        ]
    )
    ContinuousKeyframe.model_validate(payload_no_range)

    ts = TS_SHARED.read_text(encoding="utf-8")
    for token in (
        "pause_triggers",
        "at_progress",
        "duration_sec",
        "narration_keyword",
        "target_data_range",
    ):
        assert token in ts, f"shared_types.ts missing pause trigger field: {token}"


# ---------------------------------------------------------------------------
# AC-7: ThemeConfig structure (color_palette[], bg_color, font, chart_style x4, subtitle_style)
# ---------------------------------------------------------------------------
def test_theme_config_structure():
    expected = {
        "color_palette",
        "background_color",
        "font_family",
        "chart_style",
        "subtitle_style",
    }
    assert set(ThemeConfig.model_fields.keys()) == expected

    chart_expected = {
        "axis_color",
        "grid_color",
        "label_font_size",
        "tooltip_style",
    }
    assert set(ThemeChartStyle.model_fields.keys()) == chart_expected

    model = ThemeConfig.model_validate(_valid_theme_config())
    assert isinstance(model.color_palette, list)
    assert model.chart_style.label_font_size == 14

    # reject missing chart_style sub-field
    bad_chart = _valid_theme_config(
        chart_style={
            "axis_color": "#666",
            "grid_color": "#eee",
            "label_font_size": 14,
        }
    )
    with pytest.raises(ValidationError):
        ThemeConfig.model_validate(bad_chart)

    ts = TS_SHARED.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+ThemeConfig\b", ts)
    for token in ("color_palette", "chart_style", "tooltip_style", "subtitle_style"):
        assert token in ts


# ---------------------------------------------------------------------------
# AC-8: TemplateProps (union of Discrete|Continuous keyframes)
# ---------------------------------------------------------------------------
def test_template_props_union_keyframes():
    expected = {
        "templateId",
        "data",
        "chart_material",
        "annotationKeyframes",
        "timelineSegment",
        "theme",
        "fps",
    }
    assert set(TemplateProps.model_fields.keys()) == expected

    model = TemplateProps.model_validate(_valid_template_props())
    assert len(model.annotationKeyframes) == 2
    # discriminator picks the right subclass
    assert isinstance(model.annotationKeyframes[0], DiscreteKeyframe)
    assert isinstance(model.annotationKeyframes[1], ContinuousKeyframe)

    # timelineSegment shape
    ts_model = TimelineSegmentRange.model_validate({"startFrame": 0, "endFrame": 90})
    assert ts_model.endFrame == 90

    # invalid keyframe type rejected
    bad = _valid_template_props(annotationKeyframes=[{"type": "unknown", "foo": "bar"}])
    with pytest.raises(ValidationError):
        TemplateProps.model_validate(bad)

    ts = TS_TEMPLATE.read_text(encoding="utf-8")
    assert re.search(r"\binterface\s+TemplateProps\b", ts)
    assert "DiscreteKeyframe" in ts and "ContinuousKeyframe" in ts
    # union syntax present
    assert re.search(r"DiscreteKeyframe\s*\|\s*ContinuousKeyframe", ts)


# ---------------------------------------------------------------------------
# AC-9: style_lock ownership documented
# ---------------------------------------------------------------------------
def test_style_lock_ownership_constants():
    assert STYLE_LOCK_OWNERSHIP["write_agent"] == "StoryboardAgent"
    assert set(STYLE_LOCK_OWNERSHIP["read_agents"]) >= {
        "KeyframeRenderAgent",
        "ThemeConfig",
    }
    assert STYLE_LOCK_OWNERSHIP["write_phase"] == 7
    # The constant must also reference SPEC-0A.6 storage/interface basics
    assert "phases.style_lock_path" in STYLE_LOCK_OWNERSHIP["storage_field"]
