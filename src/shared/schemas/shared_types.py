"""Pydantic models for cross-module shared types (SPEC-0A.6, SPEC-0A.7).

These types are referenced by multiple SPEC areas (B/C/D/E/F) and the
authority for their field definitions lives here. Any other module that
needs the same concept MUST import from this module rather than redefining
it locally.

`STYLE_LOCK_OWNERSHIP` encodes the SPEC-0A.6 rule: StoryboardAgent at P7
writes the lock, KeyframeRenderAgent (P8) and the Remotion ThemeConfig read
it. Storage field is `phases.style_lock_path`.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

TrustLevel = Literal["user_verified", "source_verified", "llm_generated"]
TRUST_LEVEL_VALUES: tuple[TrustLevel, ...] = (
    "user_verified",
    "source_verified",
    "llm_generated",
)

HighlightType = Optional[Literal["key_data", "percentage", "number", "proper_noun"]]
HIGHLIGHT_TYPE_VALUES: tuple[str | None, ...] = (
    "key_data",
    "percentage",
    "number",
    "proper_noun",
    None,
)

DiscreteAction = Literal["highlight", "zoom_in", "zoom_out", "annotate", "dim", "reset"]
DISCRETE_ACTION_VALUES: tuple[DiscreteAction, ...] = (
    "highlight",
    "zoom_in",
    "zoom_out",
    "annotate",
    "dim",
    "reset",
)

ContinuousEasing = Literal["linear", "ease_in", "ease_out", "ease_in_out"]
CONTINUOUS_EASING_VALUES: tuple[ContinuousEasing, ...] = (
    "linear",
    "ease_in",
    "ease_out",
    "ease_in_out",
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class KeyDataPoint(_Strict):
    data_point_id: str = Field(pattern=r"^dp_[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1)
    value: str | float | int
    unit: str
    source: str = Field(min_length=1)
    trust_level: TrustLevel
    segment_id: str = Field(min_length=1)
    usage: str | None = None
    link: str | None = None


class VoiceParams(_Strict):
    voice_id: str = Field(min_length=1)
    style: str
    style_degree: float = Field(ge=0.01, le=2.0)
    rate_wpm: float = Field(gt=0)
    pitch: float
    volume: float


class SegmentVoiceOverrides(_Strict):
    rate_multiplier: float = Field(ge=0.8, le=1.2)
    emotion: str = Field(min_length=1)
    style_degree: float = Field(ge=0.01, le=2.0)
    emphasis_words: list[str]
    volume: float


class SubtitleWord(_Strict):
    word: str = Field(min_length=1)
    start_sec: float = Field(ge=0)
    end_sec: float = Field(ge=0)
    highlight_type: HighlightType = None


class ProgressMapping(_Strict):
    progress: float = Field(ge=0.0, le=1.0)
    data_index: int = Field(ge=0)
    label: str | None = None


class PauseTrigger(_Strict):
    at_progress: float = Field(ge=0.0, le=1.0)
    duration_sec: float = Field(ge=0)
    narration_keyword: str = Field(min_length=1)
    action: str = Field(min_length=1)
    target_data_range: tuple[int, int] | None = None


class DiscreteKeyframe(_Strict):
    type: Literal["discrete"]
    time_offset_sec: float = Field(ge=0)
    action: DiscreteAction
    target: str = Field(min_length=1)
    annotation: str | None = None


class ContinuousKeyframe(_Strict):
    type: Literal["continuous"]
    start_sec: float = Field(ge=0)
    end_sec: float = Field(ge=0)
    easing: ContinuousEasing
    progress_mapping: list[ProgressMapping] = Field(min_length=1)
    pause_triggers: list[PauseTrigger] | None = None


AnnotationKeyframe = Annotated[
    DiscreteKeyframe | ContinuousKeyframe,
    Field(discriminator="type"),
]


class ThemeChartStyle(_Strict):
    axis_color: str = Field(min_length=1)
    grid_color: str = Field(min_length=1)
    label_font_size: int = Field(ge=1)
    tooltip_style: dict[str, Any]


class ThemeConfig(_Strict):
    color_palette: list[str] = Field(min_length=1)
    background_color: str = Field(min_length=1)
    font_family: str = Field(min_length=1)
    chart_style: ThemeChartStyle
    subtitle_style: dict[str, Any]


# SPEC-0A.6: style_lock state ownership. Programmatic reference for anyone
# implementing read/write paths around phases.style_lock_path.
STYLE_LOCK_OWNERSHIP: dict[str, Any] = {
    "storage_field": "phases.style_lock_path",
    "file_path_template": "data/projects/{project_id}/phase_7/style_lock.json",
    "write_agent": "StoryboardAgent",
    "write_phase": 7,
    "write_api": "POST /api/projects/{id}/preferences/confirm",
    "read_agents": ("KeyframeRenderAgent", "ThemeConfig"),
    "read_phase": 8,
    "read_api": "GET /api/projects/{id}/phases/7/artifact",
    "unlock_api": "POST /api/projects/{id}/rollback",
}


__all__ = [
    "AnnotationKeyframe",
    "CONTINUOUS_EASING_VALUES",
    "ContinuousEasing",
    "ContinuousKeyframe",
    "DISCRETE_ACTION_VALUES",
    "DiscreteAction",
    "DiscreteKeyframe",
    "HIGHLIGHT_TYPE_VALUES",
    "HighlightType",
    "KeyDataPoint",
    "PauseTrigger",
    "ProgressMapping",
    "STYLE_LOCK_OWNERSHIP",
    "SegmentVoiceOverrides",
    "SubtitleWord",
    "TRUST_LEVEL_VALUES",
    "ThemeChartStyle",
    "ThemeConfig",
    "TrustLevel",
    "VoiceParams",
]
