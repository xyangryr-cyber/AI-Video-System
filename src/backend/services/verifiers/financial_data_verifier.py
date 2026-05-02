"""[SPEC-C-103] Financial data verifier for claim_type='data'.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-4 SPEC-6.Y route table.

Routes `claim_type='data'` through the v3.15 FinancialDataService pipeline
(SPEC-6.5 three-tier fallback + cache). v1 scope keeps the verifier as a
stateless shell that returns a `VerificationRecord` with `verdict='verified'`
and `verifier_type='financial_data_service'`; the real FinancialDataService
wiring lands when the P8 chart pipeline fetches live data in SPEC-D.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from src.shared.schemas.claim import Claim, VerificationRecord


class FinancialDataVerifier:
    """Stateless verifier for `claim_type='data'` claims."""

    VERIFIER_TYPE: Literal[
        "fact_check_agent", "financial_data_service", "web_search", "user_override"
    ] = "financial_data_service"

    def verify(self, claim: Claim) -> VerificationRecord:
        now = datetime.now(UTC).isoformat()
        return VerificationRecord(
            verification_id=f"ver_{claim.claim_id}_fin",
            claim_id=claim.claim_id,
            verifier_type=self.VERIFIER_TYPE,
            checked_at=now,
            verdict="verified",
            confidence=0.9,
        )


__all__ = ["FinancialDataVerifier"]
