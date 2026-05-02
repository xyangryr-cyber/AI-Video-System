"""[SPEC-D-008] P10 AVSyncReviewer -- pure L1 AV sync check.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.10.6

Placed outside reviewers/ to avoid circular import.
"""

from __future__ import annotations

from typing import Any, Dict


class AVSyncReviewer:
    """Pure L1 AV sync reviewer: checks offset against tolerance."""

    @staticmethod
    def review(
        *, rough_cut: Dict[str, Any], max_offset_ms: float = 100.0
    ) -> Dict[str, Any]:
        offset = rough_cut.get("av_offset_ms", 0.0)
        if offset > max_offset_ms:
            return {
                "verdict": "FAIL",
                "detail": f"AV offset {offset}ms exceeds {max_offset_ms}ms",
            }
        return {"verdict": "PASS"}
