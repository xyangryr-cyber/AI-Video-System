"""[SPEC-A-014] SfxLayoutPlan schema (Pydantic).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-2.

The global SFX layout plan is the upstream artifact produced by
SfxLayoutPlanner (P6 layer). Downstream SfxSegmentMixService consumes it
to produce per-segment sfx_mix_segments.json. Keep in lockstep with
`schemas/sfx_layout_plan.schema.json` and
`src/shared/types/sfx_layout_plan.ts`.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

_TRIGGER_ID_RE = r"^trg_\d{3,}$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SfxScriptAnchor(_Strict):
    """Reference to the script span that drove this SFX trigger."""

    span_id: str = Field(min_length=1)
    text: str = Field(min_length=1)


class SfxLayoutTrigger(_Strict):
    """One SFX trigger in the global layout plan."""

    trigger_id: str = Field(pattern=_TRIGGER_ID_RE)
    script_anchor: SfxScriptAnchor
    keyword_span: list[int] = Field(min_length=2, max_length=2)
    planned_time_sec: float = Field(ge=0)
    sfx_type: str = Field(min_length=1)
    rationale: str = Field(min_length=1)
    narrative_role: str = Field(min_length=1)
    volume_db: float
    duration_seconds: float = Field(ge=0)

    def model_post_init(self, __context: object) -> None:
        for v in self.keyword_span:
            if v < 0:
                raise ValueError(f"keyword_span values must be >= 0; got {self.keyword_span}")


class SfxLayoutPlan(_Strict):
    """Global SFX layout plan — consumed to produce sfx_mix_segments.json."""

    plan_version: int = Field(ge=1)
    triggers: list[SfxLayoutTrigger]


__all__ = [
    "SfxLayoutPlan",
    "SfxLayoutTrigger",
    "SfxScriptAnchor",
]
