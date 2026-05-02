"""[SPEC-D-011] L2Reviewer -- LLM-backed semantic review framework.

Authority: docs/specs/SPEC-D-pipeline-phases.md "L2 Reviewer Framework"

Placed outside reviewers/ package to avoid circular import.
"""

from __future__ import annotations

from typing import Any, Dict

from src.backend.agents.base_reviewer import BaseReviewer


class L2Reviewer(BaseReviewer):
    """Base class for L2 LLM reviewers. Tracks tokens, cost.

    In V1, review_semantic() is a stub that returns PASS.
    Production subclasses inject an LLM-backed callable.
    """

    def review_semantic(self, artifact: Any) -> Dict[str, Any]:
        """Override in subclasses. Returns standard verdict."""
        return {"verdict": "PASS", "notes": ["L2 semantic stub"]}

    def review(self, artifact: Any) -> Dict[str, Any]:
        l2 = self.review_semantic(artifact)
        return {
            "verdict": l2.get("verdict", "PASS"),
            "notes": l2.get("notes", []),
            "blocking_issues": l2.get("blocking_issues", []),
            "input_tokens": l2.get("input_tokens", 0),
            "output_tokens": l2.get("output_tokens", 0),
            "cost_usd": l2.get("cost_usd", 0.0),
        }
