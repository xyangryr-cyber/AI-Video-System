"""[SPEC-D-002..004] Pydantic response models for Agent LLM structured output.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.0.1..9.3
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


def _coerce_str_list(v: object) -> list[str]:
    """Coerce a single string or list of strings into a list of strings."""
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    if isinstance(v, list):
        return [str(item) for item in v]
    return [str(v)]


def _coerce_list(v: object) -> list[Any]:
    """Coerce a single item, dict values, or list into a list."""
    if v is None:
        return []
    if isinstance(v, list):
        return v
    if isinstance(v, dict):
        # LLM sometimes returns {key: item} instead of [{key: item, ...}]
        return list(v.values())
    return [v]


# -- RequirementsAgent (P0) -----------------------------------------------


class VoicePreferences(BaseModel):
    gender: str = "neutral"
    tone: str = "professional"
    speed: str = "medium"


class SubtitlePreferences(BaseModel):
    position: str = "bottom"
    font_size: str = "medium"


class RequirementsLLMOutput(BaseModel):
    clarified_topic: str = Field(
        ..., description="Structured topic description, not a verbatim copy of input"
    )
    voice_preferences: VoicePreferences = Field(default_factory=VoicePreferences)
    subtitle_preferences: SubtitlePreferences = Field(default_factory=SubtitlePreferences)


# -- OutlineAgent (P1) ---------------------------------------------------


class NarrativeBeat(BaseModel):
    type: str = Field(
        default="analysis", description="Beat type: hook/context/argument/climax/conclusion"
    )
    title: str = Field(default="未命名段落", description="Beat title")
    viewpoint: str = Field(default="待分析", description="Core viewpoint of this beat")
    start_seconds: int = Field(default=0, description="Start time offset in seconds")
    end_seconds: int = Field(default=60, description="End time offset in seconds")
    transition_to_next: str = ""
    supporting_data: list[str] = Field(default_factory=list)
    key_points: list[str] = Field(default_factory=list)

    @field_validator("supporting_data", "key_points", mode="before")
    @classmethod
    def _coerce_str_to_list(cls, v: object) -> list[str]:
        return _coerce_str_list(v)


class OutlineVersion(BaseModel):
    version_id: str
    viewpoint: str
    narrative_beats: list[NarrativeBeat]
    estimated_word_count: dict[str, int] = Field(default_factory=dict)


class OutlineLLMOutput(BaseModel):
    versions: list[OutlineVersion]

    @model_validator(mode="before")
    @classmethod
    def _coerce_versions(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        versions = data.get("versions")

        if isinstance(versions, dict):
            result = []
            for key, val in versions.items():
                if isinstance(val, dict):
                    val["version_id"] = val.get("version_id", key)
                    _coerce_beats(val)
                    _coerce_narrative_beats(val)
                    result.append(val)
            data["versions"] = result
        elif isinstance(versions, list):
            for v in versions:
                if isinstance(v, dict):
                    _coerce_beats(v)
                    _coerce_narrative_beats(v)
        elif versions is None:
            result = []
            for key, val in data.items():
                if key not in ("versions",) and isinstance(val, dict):
                    val["version_id"] = val.get("version_id", key)
                    _coerce_beats(val)
                    _coerce_narrative_beats(val)
                    result.append(val)
            if result:
                data["versions"] = result

        return data


def _coerce_beats(version: dict) -> None:
    """Map LLM's 'beats' to schema's 'narrative_beats'."""
    if "beats" in version and "narrative_beats" not in version:
        version["narrative_beats"] = version.pop("beats")


def _coerce_narrative_beats(version: dict) -> None:
    """Map LLM's 'beat'/'narrative' to schema's 'type'/'key_points'."""
    beats = version.get("narrative_beats")
    if not isinstance(beats, list):
        return
    for b in beats:
        if not isinstance(b, dict):
            continue
        if "beat" in b and "type" not in b:
            b["type"] = b.pop("beat")
        if "narrative" in b:
            if not b.get("key_points"):
                val = b.pop("narrative")
                b["key_points"] = [val] if isinstance(val, str) else val
            else:
                b.pop("narrative", None)
        if "version" in b:
            b.pop("version", None)


# -- ScriptAgent (P2) ----------------------------------------------------


class DataPoint(BaseModel):
    data_point_id: str = Field(
        default="dp_auto", description="Unique identifier for this data point"
    )
    value: str = Field(default="待补充", description="Data value or statement")
    source: str = "llm_generated"
    trust_level: str = "llm_generated"


class ScriptSegment(BaseModel):
    segment_id: str = Field(default="seg_auto", description="Unique segment identifier")
    section_title: str = Field(default="未命名段落", description="Section title")
    outline_section_ref: str = Field(default="auto", description="Reference to outline section")
    content: str = Field(default="待生成", description="Narration script content")
    word_count: int = Field(default=0, description="Word count for this segment")
    key_data_points: list[DataPoint] = Field(default_factory=list)
    emotion_tone: str = "neutral"
    transition_note: str = ""


class ScriptLLMOutput(BaseModel):
    segments: list[ScriptSegment]


# -- PolishAgent (P3) ----------------------------------------------------


class VoiceDirection(BaseModel):
    emotion: str
    pace: str
    energy: str
    key_emphasis: list[str] = Field(default_factory=list)
    pause_after: float = 0.3
    notes: str = ""


class PolishedSegment(BaseModel):
    segment_id: str = Field(default="seg_auto", description="Unique segment identifier")
    section_title: str = Field(default="未命名段落", description="Section title")
    outline_section_ref: str = Field(default="auto", description="Reference to outline section")
    content: str = Field(default="待生成", description="Polished narration content")
    word_count: int = Field(default=0, description="Word count for this segment")
    key_data_points: list[dict[str, Any]] = Field(default_factory=list)
    emotion_tone: str = "neutral"
    transition_note: str = ""
    voice_direction: VoiceDirection = Field(
        default_factory=lambda: VoiceDirection(emotion="neutral", pace="medium", energy="medium")
    )


class PolishLLMOutput(BaseModel):
    segments: list[PolishedSegment]
    is_authoritative_text_source: bool = True


__all__ = [
    "DataPoint",
    "NarrativeBeat",
    "OutlineLLMOutput",
    "OutlineVersion",
    "PolishedSegment",
    "PolishLLMOutput",
    "RequirementsLLMOutput",
    "ScriptLLMOutput",
    "ScriptSegment",
    "SubtitlePreferences",
    "VoiceDirection",
    "VoicePreferences",
]
