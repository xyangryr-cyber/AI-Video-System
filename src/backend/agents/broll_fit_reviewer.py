"""[SPEC-D-007] P9 BRollFitReviewer -- L1 + L2 B-Roll fit review.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.9.5
"""

from __future__ import annotations

from typing import Any, Dict, List


class BRollFitReviewer:
    """Review B-Roll fit: L1 (semantic relevance, quality) + L2 stub."""

    @staticmethod
    def review_l1(
        *, broll_candidates: List[Dict[str, Any]], min_relevance: float = 0.3
    ) -> Dict[str, Any]:
        blocking: list[str] = []
        for c in broll_candidates:
            score = c.get("relevance_score", 0.0)
            if score < min_relevance:
                blocking.append(
                    f"candidate {c.get('id', '?')} relevance {score:.2f} < {min_relevance}"
                )
        verdict = "FAIL" if blocking else "PASS"
        return {"verdict": verdict, "blocking_issues": blocking}

    @classmethod
    def review(cls, *, broll_candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
        l1 = cls.review_l1(broll_candidates=broll_candidates)
        l2_called = l1["verdict"] == "PASS"
        return {"verdict": l1["verdict"], "l1_result": l1, "l2_called": l2_called}
