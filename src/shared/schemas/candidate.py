"""Pydantic models for Candidate (SPEC-0A.2).

Candidate is the aesthetic-choice payload emitted by phase agents
(P4 TTS / P5 BGM / P7 Storyboard / P8 Keyframe / P9 Cover) and rendered
by the frontend `CandidateSelector`. Each phase may emit at most three
candidates; the container `CandidateList` enforces that upper bound.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional, Tuple

from pydantic import BaseModel, ConfigDict, Field

PreviewType = Literal["audio", "image", "video", "color_palette"]

PREVIEW_TYPES: Tuple[PreviewType, ...] = (
    "audio",
    "image",
    "video",
    "color_palette",
)


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Candidate(_Strict):
    candidate_id: str = Field(pattern=r"^cand_[A-Za-z0-9_-]+$")
    preview_url: str = Field(min_length=1)
    preview_type: PreviewType
    style_tags: List[str]
    description: str = Field(min_length=1)
    is_recommended: bool
    adjustable_params: Dict[str, Any]
    rationale: str = Field(min_length=1)
    raw_bgm_url: Optional[str] = None


class CandidateList(_Strict):
    """Container enforcing the SPEC-0A.2 rule that candidates count <= 3."""

    candidates: List[Candidate] = Field(max_length=3)


__all__ = [
    "PREVIEW_TYPES",
    "Candidate",
    "CandidateList",
    "PreviewType",
]
