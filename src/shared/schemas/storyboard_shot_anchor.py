"""Pydantic models for [SPEC-A-103] StoryboardShotAnchor.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-4 (SPEC-0A.12).

Each P7 shot JSON file (``phase_7/shots/shot_NN.json``) MUST carry a
top-level ``anchor`` field of this type so that downstream phases
(P8 keyframe, P9 broll, P10 roughcut) can locate the exact
``polished_script`` span the shot corresponds to. The programmatic
substring invariant ``polished_script[start_char:end_char] ==
anchor_text`` is enforced by the P7 agent at write time (SPEC
§A-BDD-4 AC bullet 2), not by this schema.

Mirrored in TypeScript by
``src/shared/types/storyboard_shot_anchor.ts``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DownstreamBindings(BaseModel):
    """Optional pointers from a P7 shot into downstream phases.

    Each of the three fields is optional: a shot may be bound to a P8
    template, a P9 broll clip, and/or a P10 track in any combination,
    including none at all (default).
    """

    model_config = ConfigDict(extra="forbid")

    p8_template_shot_id: Optional[str] = None
    p9_broll_shot_id: Optional[str] = None
    p10_track_ref: Optional[str] = None


class StoryboardShotAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shot_id: str = Field(min_length=1)
    anchor_text: str = Field(min_length=1, max_length=200)
    script_span_id: str = Field(min_length=1)
    start_char: int = Field(ge=0)
    end_char: int = Field(ge=0)
    split_from_shot_id: Optional[str] = None
    downstream_bindings: DownstreamBindings = Field(default_factory=DownstreamBindings)

    @model_validator(mode="after")
    def _end_not_before_start(self) -> "StoryboardShotAnchor":
        if self.end_char < self.start_char:
            raise ValueError(
                f"end_char ({self.end_char}) must be >= start_char "
                f"({self.start_char}); anchor text span is inverted"
            )
        return self


__all__ = ["DownstreamBindings", "StoryboardShotAnchor"]
