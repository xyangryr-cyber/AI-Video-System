"""[SPEC-D-003] P2 FactChecker -- L1 source reachability + L2 semantic comparison.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.2.3

Placed outside the reviewers/ package to avoid the known circular import:
reviewers/__init__.py -> l1_checks -> reviewer_agent -> l1_checks (loop).
Same pattern as CompletenessReviewer (D-002).
"""

from __future__ import annotations

from typing import Any


class FactChecker:
    """Dual-layer fact checker for per-segment data points.

    L1: source reachability (URL well-formedness check)
    L2: semantic comparison stub (LLM-backed in production)
    """

    @staticmethod
    def check_l1(data_point: dict[str, Any]) -> dict[str, Any]:
        """Check whether a single data point's source is well-formed."""
        source = data_point.get("source", "")
        if not source:
            return {
                "data_point_id": data_point.get("data_point_id", "?"),
                "verdict": "FAIL",
                "reason": "empty source",
            }
        # Check URL well-formedness
        if source.startswith("http://") or source.startswith("https://"):
            return {
                "data_point_id": data_point.get("data_point_id", "?"),
                "verdict": "PASS",
            }
        return {
            "data_point_id": data_point.get("data_point_id", "?"),
            "verdict": "FAIL",
            "reason": f"source not a well-formed URL: {source!r}",
        }

    @staticmethod
    def check_l2(data_point: dict[str, Any]) -> dict[str, Any]:
        """L2 semantic comparison stub (LLM-backed in production)."""
        return {
            "data_point_id": data_point.get("data_point_id", "?"),
            "verdict": "PASS",
            "note": "L2 semantic check not yet implemented (requires LLM key)",
        }

    @classmethod
    def review(cls, segments: list[dict[str, Any]]) -> dict[str, Any]:
        """Review all data points across segments.

        - L1: check source reachability for every data point
        - llm_generated data points with empty source -> FAIL
        """
        notes: list[str] = []
        blocking: list[str] = []

        for seg in segments:
            for dp in seg.get("key_data_points", []):
                l1_result = cls.check_l1(dp)
                if l1_result["verdict"] == "FAIL":
                    blocking.append(
                        f"{dp.get('data_point_id')}: {l1_result.get('reason', 'L1 FAIL')}"
                    )

        # Also fail if any llm_generated data point lacks source
        for seg in segments:
            for dp in seg.get("key_data_points", []):
                if dp.get("trust_level") == "llm_generated" and not dp.get("source"):
                    blocking.append(
                        f"llm_generated data point {dp.get('data_point_id')} has no source"
                    )

        verdict = "FAIL" if blocking else "PASS"
        if not blocking:
            notes.append("All data points pass L1 source check")

        return {"verdict": verdict, "notes": notes, "blocking_issues": blocking}
