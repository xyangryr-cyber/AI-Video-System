"""[SPEC-C-101] challenge_claim action params (v3.16 C-BDD-2).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-2.

Idempotency: (claim_id, SHA-256(evidence_url)) — 24 h.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ChallengeClaimParams(BaseModel):
    """Params for a user's challenge against a previously stated claim."""

    model_config = ConfigDict(extra="forbid")

    claim_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    evidence_url: str | None = None


__all__ = ["ChallengeClaimParams"]
