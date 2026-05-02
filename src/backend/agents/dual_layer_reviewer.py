"""[SPEC-D-011] DualLayerReviewer -- composes L1 + L2, gates L2 on L1 PASS.

Authority: docs/specs/SPEC-D-pipeline-phases.md "Dual-Layer Reviewer"

Placed outside reviewers/ package to avoid circular import.
"""

from __future__ import annotations

from typing import Any, Dict

from src.backend.agents.l1_reviewer import L1Reviewer
from src.backend.agents.l2_reviewer import L2Reviewer


class DualLayerReviewer:
    """Compose L1 (programmatic) + L2 (LLM) reviewers.

    L2 only runs when L1 passes, saving tokens when L1 already found issues.
    """

    def __init__(self, *, l1_reviewer: L1Reviewer, l2_reviewer: L2Reviewer) -> None:
        self._l1 = l1_reviewer
        self._l2 = l2_reviewer

    def review(self, artifact: Any) -> Dict[str, Any]:
        l1_result = self._l1.review(artifact)

        if l1_result["verdict"] == "FAIL":
            return {
                "verdict": "FAIL",
                "blocking_issues": l1_result["blocking_issues"],
                "notes": l1_result["notes"],
                "l2_triggered": False,
                "l2_token_cost": 0,
            }

        l2_result = self._l2.review(artifact)
        merged_blocking = l1_result.get("blocking_issues", []) + l2_result.get(
            "blocking_issues", []
        )
        return {
            "verdict": l2_result.get("verdict", "PASS"),
            "blocking_issues": merged_blocking,
            "notes": l1_result.get("notes", []) + l2_result.get("notes", []),
            "l2_triggered": True,
            "l2_token_cost": l2_result.get("input_tokens", 0)
            + l2_result.get("output_tokens", 0),
        }
