"""[SPEC-C-101] supplement_claim action params (v3.16 C-BDD-2).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-2.

Idempotency: (SHA-256(text), source_phase) — 1 h.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ClaimType = Literal["fact", "data", "event", "citation", "image_backed"]
SourcePhase = Literal["P2", "P7", "P8", "P9", "user_input"]


class SupplementClaimParams(BaseModel):
    """Params for a user-authored supplementary claim fed back into the pipeline."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1)
    claim_type: ClaimType
    source_phase: SourcePhase
    source_artifact: str = Field(min_length=1)
    source_span: str | None = None


__all__ = ["ClaimType", "SourcePhase", "SupplementClaimParams"]
