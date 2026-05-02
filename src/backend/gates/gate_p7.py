"""[SPEC-D-006] Gate-P7: validates P7 outputs before advancing to P8.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.7.8
"""

from __future__ import annotations

from typing import Any, Dict, List


class GateP7:
    """Check: storyboard complete, style_lock exists, reviewer PASS,
    audit#1 INCONSISTENCY=0, no pending tasks, preferences confirmed."""

    @staticmethod
    def check(
        *,
        storyboard_complete: bool,
        style_lock_exists: bool,
        reviewer_passed: bool,
        audit_inconsistency: int,
        pending_tasks: List[Any],
        preferences_confirmed: bool,
    ) -> Dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        if not storyboard_complete:
            failed.append("storyboard JSON incomplete")
        else:
            passed.append("storyboard complete")

        if not style_lock_exists:
            failed.append("style_lock.json missing")
        else:
            passed.append("style_lock exists")

        if not reviewer_passed:
            failed.append("StoryboardReviewer FAIL")
        else:
            passed.append("StoryboardReviewer PASS")

        if audit_inconsistency != 0:
            failed.append(f"audit #1 has {audit_inconsistency} inconsistencies")
        else:
            passed.append("audit #1 clean")

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
