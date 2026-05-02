"""[SPEC-A-014] SfxMixSegments schema (Pydantic).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-2.

The per-segment SFX mix artifact produced by SfxSegmentMixService; its
`base_master` must reference an upstream master (narration_master or
bgm_mix_master). Cross-artifact consistency against SfxLayoutPlan is
enforced via `validate_applied_triggers_against_plan`. Keep in lockstep
with `schemas/sfx_mix_segments.schema.json` and
`src/shared/types/sfx_mix_segments.ts`.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict, Field

from src.shared.schemas.sfx_layout_plan import SfxLayoutPlan

_SEGMENT_ID_RE = r"^seg_\d{2,}$"
_TRIGGER_ID_RE = r"^trg_\d{3,}$"
_CHECKSUM_RE = r"^sha256:[a-f0-9]{64}$"
_FILE_PATH_RE = r"^phase_6/sfx_applied_segments/seg_\d{2,}\.mp3$"
# base_master must point at an existing upstream master (P4 narration or P5 BGM).
BASE_MASTER_RE = r"^(phase_5/bgm_mix_master|phase_4/narration_master)\.mp3$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SfxMixSegment(_Strict):
    """One per-segment SFX-applied audio produced from the base_master."""

    segment_id: str = Field(pattern=_SEGMENT_ID_RE)
    file_path: str = Field(pattern=_FILE_PATH_RE)
    applied_triggers: List[str] = Field(default_factory=list)
    checksum: str = Field(pattern=_CHECKSUM_RE)
    version: int = Field(ge=1)

    def model_post_init(self, __context: object) -> None:
        import re

        pat = re.compile(_TRIGGER_ID_RE)
        for trigger_id in self.applied_triggers:
            if not pat.match(trigger_id):
                raise ValueError(
                    f"applied_triggers contains invalid id {trigger_id!r} "
                    f"(expected pattern {_TRIGGER_ID_RE})"
                )


class SfxMixSegments(_Strict):
    """Local SFX mix artifact — N segments derived from one base_master."""

    base_master: str = Field(pattern=BASE_MASTER_RE)
    segments: List[SfxMixSegment]


def validate_applied_triggers_against_plan(
    mix: SfxMixSegments,
    plan: SfxLayoutPlan,
) -> None:
    """AC-5 invariant: every trigger_id in `mix.segments[].applied_triggers`
    MUST exist in `plan.triggers[].trigger_id`.

    Raises ValueError on any orphan trigger_id.
    """
    plan_ids = {t.trigger_id for t in plan.triggers}
    orphans: list[tuple[str, str]] = []
    for seg in mix.segments:
        for trigger_id in seg.applied_triggers:
            if trigger_id not in plan_ids:
                orphans.append((seg.segment_id, trigger_id))
    if orphans:
        details = ", ".join(f"{s}->{t}" for s, t in orphans)
        raise ValueError(
            "applied_triggers references trigger_id(s) not in "
            f"sfx_layout_plan.triggers: {details}"
        )


__all__ = [
    "BASE_MASTER_RE",
    "SfxMixSegment",
    "SfxMixSegments",
    "validate_applied_triggers_against_plan",
]
