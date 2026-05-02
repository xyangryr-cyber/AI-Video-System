"""[SPEC-D-101] SupplementClaimCard — user supplement scenario card.

Authority: docs/specs/SPEC-D-pipeline-phases.md §D-BDD-2

Handles:
- supplement_claim: creates a new claim, enqueues it, marks downstream as blocked
"""

from __future__ import annotations

import hashlib
import time
from typing import Any, Literal


class SupplementClaimCard:
    """Scenario card for user supplementary claims."""

    def handle(
        self,
        *,
        text: str,
        claim_type: Literal["fact", "data", "event", "citation", "image_backed"],
        source_phase: str,
        source_artifact: str,
    ) -> dict[str, Any]:
        """Create a new claim from user supplement, block downstream flow.

        The new claim is created with blocking_level='hard' to ensure Gates
        wait for verification, and verification_status='pending'.
        """
        now = time.time()
        claim_id = f"claim_supplement_{hashlib.sha256(text.encode('utf-8')).hexdigest()[:12]}"

        new_claim: dict[str, Any] = {
            "claim_id": claim_id,
            "claim_type": claim_type,
            "text": text,
            "source_phase": source_phase,
            "source_artifact": source_artifact,
            "blocking_level": "hard",
            "verification_status": "pending",
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(now)),
        }

        return {
            "new_claim": new_claim,
            "blocked": True,
            "reason": "supplement claim enqueued, downstream gates will block until verified",
        }


__all__ = ["SupplementClaimCard"]
