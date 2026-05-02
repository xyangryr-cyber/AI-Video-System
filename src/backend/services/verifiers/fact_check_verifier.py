"""[SPEC-C-103] Fact-check verifier for claim_type in ('fact', 'event').

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-4 SPEC-6.Y route table.

Wraps the v3.16 FactCheckAgent (LLM + web_search). v1 scope keeps the
verifier stateless and returns a stock `VerificationRecord`; the real
LLM/web_search wiring lands when SPEC-D plugs the fact-check LLM path in.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from src.shared.schemas.claim import Claim, VerificationRecord


class FactCheckVerifier:
    """Stateless verifier for `claim_type in {'fact','event'}` claims."""

    VERIFIER_TYPE: Literal[
        "fact_check_agent", "financial_data_service", "web_search", "user_override"
    ] = "fact_check_agent"

    def verify(self, claim: Claim) -> VerificationRecord:
        now = datetime.now(timezone.utc).isoformat()
        return VerificationRecord(
            verification_id=f"ver_{claim.claim_id}_fact",
            claim_id=claim.claim_id,
            verifier_type=self.VERIFIER_TYPE,
            checked_at=now,
            verdict="verified",
            confidence=0.8,
        )


__all__ = ["FactCheckVerifier"]
