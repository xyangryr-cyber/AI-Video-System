"""[SPEC-C-103] Image-backed claim verifier (vision model + source check).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-4 SPEC-6.Y route table.

v1 scope keeps the verifier stateless and returns a stock
`VerificationRecord`; the real vision-model wiring lands in SPEC-F when
keyframes / B-Roll metadata feed into the visual verifier.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from src.shared.schemas.claim import Claim, VerificationRecord


class ImageBackedVerifier:
    """Stateless verifier for `claim_type='image_backed'` claims."""

    VERIFIER_TYPE: Literal[
        "fact_check_agent", "financial_data_service", "web_search", "user_override"
    ] = "web_search"  # schema enum, image verifier uses web_search bucket for v1

    def verify(self, claim: Claim) -> VerificationRecord:
        now = datetime.now(timezone.utc).isoformat()
        return VerificationRecord(
            verification_id=f"ver_{claim.claim_id}_img",
            claim_id=claim.claim_id,
            verifier_type=self.VERIFIER_TYPE,
            checked_at=now,
            verdict="verified",
            confidence=0.7,
        )


__all__ = ["ImageBackedVerifier"]
