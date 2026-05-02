"""[SPEC-D-101] ChallengeClaimCard — user challenge scenario card.

Authority: docs/specs/SPEC-D-pipeline-phases.md §D-BDD-2

Handles:
- challenge_claim: marks downstream artifacts damaged (via ArtifactDamageMarker)
- idempotency gate: same (claim_id, evidence_hash) within 24h => discard
- dual verification record preservation on conflict
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Dict


class ChallengeClaimCard:
    """Scenario card for user claim challenges."""

    IDEMPOTENCY_TTL_SECONDS = 24 * 3600  # 24h

    def __init__(self) -> None:
        self._idempotency_store: Dict[str, float] = {}

    def _idempotency_key(self, claim_id: str, evidence_hash: str) -> str:
        return hashlib.sha256(f"{claim_id}:{evidence_hash}".encode("utf-8")).hexdigest()

    def challenge_with_idempotency(
        self,
        *,
        claim_id: str,
        reason: str,
        evidence_hash: str,
    ) -> Dict[str, Any]:
        """Challenge a claim with idempotency gate.

        Returns {"accepted": True/False, "reason": str}.
        A duplicate (same claim_id + evidence_hash) within 24h is discarded.
        """
        key = self._idempotency_key(claim_id, evidence_hash)
        now = time.monotonic()

        if key in self._idempotency_store:
            last_ts = self._idempotency_store[key]
            if now - last_ts < self.IDEMPOTENCY_TTL_SECONDS:
                return {
                    "accepted": False,
                    "reason": f"discarded: duplicate challenge for claim {claim_id} within 24h window",
                }

        self._idempotency_store[key] = now
        return {
            "accepted": True,
            "reason": f"challenge accepted for claim {claim_id}",
        }

    def preserve_dual_records(
        self,
        *,
        old_record: Dict[str, Any],
        new_record: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Preserve both verification records when re-verify yields a different result.

        If old and new verdicts differ, both records are kept for audit trail.
        If they agree, the old one is superseded (single record returned).
        """
        conflict = old_record["verdict"] != new_record["verdict"]
        records = [old_record, new_record] if conflict else [new_record]

        return {
            "preserved_count": len(records),
            "records": records,
            "conflict": conflict,
        }


__all__ = ["ChallengeClaimCard"]
