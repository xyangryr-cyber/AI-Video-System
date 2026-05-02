"""Pydantic model for Remotion `TemplateProps` (SPEC-0A.7).

This is the single authoritative shape that backend P8 / F rendering
orchestration passes into every Remotion template. Keyframes are a
discriminated union of DiscreteKeyframe and ContinuousKeyframe from
`shared_types`.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from src.shared.schemas.chart_material import ChartMaterial
from src.shared.schemas.shared_types import (
    AnnotationKeyframe,
    ThemeConfig,
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TimelineSegmentRange(_Strict):
    startFrame: int = Field(ge=0)
    endFrame: int = Field(ge=0)


class TemplateProps(_Strict):
    templateId: str = Field(min_length=1)
    data: Any
    annotationKeyframes: list[AnnotationKeyframe]
    timelineSegment: TimelineSegmentRange
    theme: ThemeConfig
    fps: int = Field(ge=1)
    chart_material: ChartMaterial | None = Field(default=None)


__all__ = [
    "TemplateProps",
    "TimelineSegmentRange",
]
