"""[SPEC-C-017] EnvelopeSpec -- static gain + fade envelope for P5 BGM mix.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-2.

The envelope is the explicit shared input to both AudioMixPreviewService
and BgmMixRenderer so preview and master use byte-identical mix rules
(required for deterministic re-render + checksum-chain reproducibility).

Current v1 shape deliberately carries only the fields needed for the §23.9
第 3 行 gate: constant BGM attenuation + linear fade-in / fade-out. Ducking
curves and per-segment envelopes are C-018 / C-AUDP7A-3 territory.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class EnvelopeSpec(BaseModel):
    """Deterministic BGM envelope applied on top of narration.

    Fields:
      bgm_gain_db: Constant BGM attenuation in dB. MUST be <= 0 so the BGM
                   does not dominate the narration.
      fade_in_ms:  Linear fade-in applied to the BGM at t=0, in milliseconds.
      fade_out_ms: Linear fade-out applied to the BGM at the end of the
                   narration, in milliseconds.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    bgm_gain_db: float = Field(le=0.0)
    fade_in_ms: int = Field(ge=0, le=10_000)
    fade_out_ms: int = Field(ge=0, le=10_000)


__all__ = ["EnvelopeSpec"]
