"""[SPEC-D-101] ArtifactDamageMarker — mark downstream artifacts damaged within 60s SLA.

Authority: docs/specs/SPEC-D-pipeline-phases.md §D-BDD-2

When a claim is challenged, all downstream artifacts that reference that claim
must have their status flipped to 'damaged' synchronously, well within the
60-second visibility SLA.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List


class ArtifactDamageMarker:
    """Synchronously marks downstream artifacts as damaged when a claim is challenged."""

    def mark_damaged(
        self,
        *,
        claim_id: str,
        downstream_artifacts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        start = time.monotonic()
        damaged: List[Dict[str, Any]] = []

        for art in downstream_artifacts:
            if claim_id in art.get("claim_ids", []):
                damaged.append({"artifact_id": art["artifact_id"], "status": "damaged"})

        elapsed = time.monotonic() - start
        return {
            "claim_id": claim_id,
            "elapsed_seconds": round(elapsed, 4),
            "damaged_count": len(damaged),
            "damaged": damaged,
        }


__all__ = ["ArtifactDamageMarker"]
