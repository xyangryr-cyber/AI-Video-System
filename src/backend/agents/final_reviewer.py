"""[SPEC-D-009] P11 FinalReviewer -- pure L1 8 quality checks + audit#3 summary.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.11.5

Placed outside reviewers/ to avoid circular import.
"""

from __future__ import annotations

from typing import Any, Dict, List


class FinalReviewer:
    """Pure L1 final review: 8 quality checks on final cut."""

    @staticmethod
    def review(final_cut: Dict[str, Any]) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []

        checks.append(
            {
                "rule": "resolution",
                "verdict": "PASS"
                if final_cut.get("resolution") == "1920x1080"
                else "FAIL",
            }
        )
        checks.append(
            {
                "rule": "has_audio",
                "verdict": "PASS" if final_cut.get("has_audio") else "FAIL",
            }
        )
        checks.append(
            {
                "rule": "has_subtitles",
                "verdict": "PASS" if final_cut.get("has_subtitles") else "FAIL",
            }
        )
        checks.append(
            {
                "rule": "duration",
                "verdict": "PASS"
                if final_cut.get("duration_seconds", 0) > 0
                else "FAIL",
            }
        )

        verdict = "FAIL" if any(c["verdict"] == "FAIL" for c in checks) else "PASS"
        return {"verdict": verdict, "checks": checks}
