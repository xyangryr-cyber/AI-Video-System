"""Pydantic models for core artifacts (SPEC-0A.1)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


DurationClass = Literal["short", "medium", "long"]
NarrativeTemplate = Literal[
    "chronological", "progressive", "comparative", "problem_solution", "storytelling"
]
SubtitleStyle = Literal["word_by_word", "sentence"]
LockedBy = Literal["user_confirmed", "auto_recommended"]


class TargetDuration(_Strict):
    min_sec: int = Field(ge=0)
    max_sec: int = Field(ge=0)


class TargetWordCount(_Strict):
    min: int = Field(ge=0)
    max: int = Field(ge=0)


class Category(_Strict):
    level1: str = Field(min_length=1)
    level2: str = Field(min_length=1)


PlatformRole = Literal["primary", "secondary"]


class PlatformEntry(_Strict):
    platform: str = Field(min_length=1)
    role: PlatformRole


class VoicePreferences(_Strict):
    voice_id: str = Field(min_length=1)
    style: str = Field(min_length=1)


class SubtitlePreferences(_Strict):
    style: SubtitleStyle
    highlight_enabled: bool


class Requirements(_Strict):
    project_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    topic: str = Field(min_length=5)
    clarified_topic: str = Field(default="")
    duration_class: DurationClass
    target_duration_seconds: int = Field(default=600, ge=0)
    target_duration: TargetDuration
    target_word_count: TargetWordCount
    platform: list[PlatformEntry] = Field(min_length=1)
    category: Category
    narrative_template: NarrativeTemplate
    voice_preferences: VoicePreferences
    subtitle_preferences: SubtitlePreferences
    target_platform: str = Field(default="web")
    clarification_needed: list[dict[str, str]] = Field(default_factory=list)


class VoiceParams(_Strict):
    rate_multiplier: float = Field(gt=0)
    emotion: str = Field(min_length=1)


class TimelineSegment(_Strict):
    segment_id: str = Field(min_length=1)
    text: str
    start_sec: float = Field(ge=0)
    end_sec: float = Field(ge=0)
    audio_path: str = Field(min_length=1)
    voice_params: VoiceParams
    word_count: int = Field(ge=0)


class Timeline(_Strict):
    segments: list[TimelineSegment] = Field(min_length=1)
    total_duration_sec: float = Field(ge=0)
    sample_rate: int = Field(ge=1)


class ColorPalette(_Strict):
    primary: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    secondary: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    accent: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")
    background: str = Field(pattern=r"^#[0-9a-fA-F]{6}$")


class ChartStyle(_Strict):
    axis_color: str = Field(min_length=1)
    grid_color: str = Field(min_length=1)
    label_font_size: int = Field(ge=1)


class StyleLock(_Strict):
    project_id: str = Field(min_length=1)
    locked_at: str = Field(min_length=1)
    locked_by: LockedBy
    color_palette: ColorPalette
    font_family: str = Field(min_length=1)
    chart_style: ChartStyle


class PolishedScriptArtifact(_Strict):
    style_applied: str | None = None


class AnnotationSpan(_Strict):
    span_id: str = Field(min_length=1)
    text_range: tuple[int, int]
    effect: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    narrative_role: str = Field(min_length=1)


AssetStatus = Literal["not_needed", "fetched"]


class AssetSourcingEntry(_Strict):
    shot_id: str = Field(min_length=1)
    status: AssetStatus
    need: str | None = None
    action: str | None = None
    data: dict[str, Any] | None = None


RenderStatus = Literal["pending_broll", "rendered"]


class KeyframeRenderEntry(_Strict):
    shot_id: str = Field(min_length=1)
    render_status: RenderStatus
    file_name: str | None = None
    thumbnail_url: str | None = None


class BRollEntry(_Strict):
    file_name: str = Field(min_length=1)
    duration_sec: float = Field(gt=0)
    match_label: str = Field(min_length=1)
    license: str = Field(min_length=1)
    source_url: str | None = None


class DeliveryVariant(_Strict):
    platform: str = Field(min_length=1)
    resolution: str = Field(min_length=1)
    codec: str = Field(min_length=1)
    aspect_ratio: str = Field(min_length=1)
    file_size_mb: float = Field(gt=0)
    download_url: str = Field(min_length=1)


class SubtitleDownload(_Strict):
    format: str = Field(min_length=1)
    download_url: str = Field(min_length=1)


__all__ = [
    "AnnotationSpan",
    "AssetSourcingEntry",
    "AssetStatus",
    "BRollEntry",
    "Category",
    "ChartStyle",
    "ColorPalette",
    "DeliveryVariant",
    "KeyframeRenderEntry",
    "PlatformEntry",
    "PlatformRole",
    "PolishedScriptArtifact",
    "RenderStatus",
    "Requirements",
    "StyleLock",
    "SubtitleDownload",
    "SubtitlePreferences",
    "TargetDuration",
    "TargetWordCount",
    "Timeline",
    "TimelineSegment",
    "VoiceParams",
    "VoicePreferences",
]
