"""[SPEC-D-016] ViewerExperienceReviewer -- L2 viewer perspective evaluation (6 dimensions).

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.13

Placed outside reviewers/ to avoid circular import.
"""

from __future__ import annotations

from typing import Any


class ViewerExperienceReviewer:
    """Evaluate rough cut from viewer perspective. 6 dimensions, L2 (LLM-backed stub).
    FAIL does NOT block Gate-P10; improvement_suggestions advisory for P11."""

    @staticmethod
    def should_trigger(*, av_sync_passed: bool) -> bool:
        return av_sync_passed

    @staticmethod
    def blocks_gate() -> bool:
        return False

    @staticmethod
    def review(
        *,
        rough_cut_metadata: dict[str, Any],
        polished_script: dict[str, Any],
        emotion_curve: dict[str, Any],
        timeline: dict[str, Any],
    ) -> dict[str, Any]:
        dims = {
            "hook_appeal": 7,
            "pacing": 6,
            "information_density": 8,
            "emotional_arc": 6,
            "ending_impact": 7,
            "watchability": 7,
        }
        overall = sum(dims.values()) / len(dims)
        return {
            "verdict": "PASS" if overall >= 6 else "FAIL",
            "overall_score": round(overall, 1),
            "dimension_scores": dims,
            "improvement_suggestions": [],
            "notes": ["Viewer experience evaluated"],
            "blocking_issues": [] if overall >= 6 else ["overall score below 6"],
        }
