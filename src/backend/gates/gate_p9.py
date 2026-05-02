"""[SPEC-D-007] Gate-P9: validates P9 outputs before advancing to P10.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.9.7
"""

from __future__ import annotations

from typing import Any


class GateP9:
    @staticmethod
    def check(
        *,
        broll_complete: bool,
        reviewer_passed: bool,
        pending_tasks: list[Any],
        preferences_confirmed: bool,
    ) -> dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        if not broll_complete:
            failed.append("B-Roll not complete")
        else:
            passed.append("B-Roll complete")

        if not reviewer_passed:
            failed.append("BRollFitReviewer FAIL")
        else:
            passed.append("BRollFitReviewer PASS")

        if pending_tasks:
            failed.append(f"{len(pending_tasks)} pending tasks")
        else:
            passed.append("no pending tasks")

        if not preferences_confirmed:
            failed.append("preferences not confirmed")
        else:
            passed.append("preferences confirmed")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }
