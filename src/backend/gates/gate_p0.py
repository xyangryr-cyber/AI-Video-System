"""[SPEC-D-002] Gate-P0: validates P0 outputs before advancing to P1.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.0.3
"""

from __future__ import annotations

from typing import Any, Dict


class GateP0:
    """Check: requirements present, reviewer PASS, preferences confirmed."""

    @staticmethod
    def check(requirements: Dict[str, Any]) -> Dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        # 1. requirements.json exists (has required fields)
        if not requirements or not requirements.get("project_id"):
            failed.append("requirements.json missing or empty")
        else:
            passed.append("requirements.json exists")

        # 2. CompletenessReviewer verdict
        # Inline review (stateless, no DB dependency)
        from src.backend.agents.completeness_reviewer import CompletenessReviewer

        reviewer = CompletenessReviewer()
        verdict = reviewer.review(requirements)
        if verdict["verdict"] == "PASS":
            passed.append("CompletenessReviewer PASS")
        else:
            failed.append(f"CompletenessReviewer FAIL: {verdict['blocking_issues']}")

        # 3. preferences_confirmed_at non-null
        prefs = requirements.get("preferences_confirmed_at")
        if prefs:
            passed.append("preferences_confirmed")
        else:
            failed.append("preferences_confirmed_at is null")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }
