"""[SPEC-D-002] Gate-P1: validates P1 outputs before advancing to P2.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.1.x
"""

from __future__ import annotations

from typing import Any, Dict, List


class GateP1:
    """Check: selected outline exists, StructureReviewer PASS, ready to advance."""

    @staticmethod
    def check(
        outlines: List[Dict[str, Any]],
        *,
        selected_version_id: str | None = None,
    ) -> Dict[str, Any]:
        failed: list[str] = []
        passed: list[str] = []

        # 1. selected outline exists
        if not selected_version_id:
            failed.append("No outline selected")
        elif not _find_outline(outlines, selected_version_id):
            failed.append(f"Selected outline {selected_version_id!r} not found")
        else:
            passed.append(f"Outline {selected_version_id} selected")

        # 2. StructureReviewer PASS on selected version
        from src.backend.agents.structure_reviewer import StructureReviewer

        reviewer = StructureReviewer()
        verdict = reviewer.review(outlines, selected_version_id=selected_version_id)
        if verdict["verdict"] == "PASS":
            passed.append("StructureReviewer PASS")
        else:
            failed.append(f"StructureReviewer FAIL: {verdict['blocking_issues']}")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }


def _find_outline(
    outlines: List[Dict[str, Any]], version_id: str
) -> Dict[str, Any] | None:
    for o in outlines:
        if o.get("version_id") == version_id:
            return o
    return None
