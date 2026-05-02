"""[SPEC-D-003] Gate-P2: validates P2 outputs before advancing to P3.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.2.4
"""

from __future__ import annotations

from typing import Any, Dict, List


class GateP2:
    """Check: script fields complete, FactChecker PASS, StructureReviewer PASS,
    no pending tasks, preferences confirmed."""

    _REQUIRED_SEGMENT_FIELDS = frozenset(
        {
            "segment_id",
            "section_title",
            "outline_section_ref",
            "content",
            "word_count",
            "key_data_points",
            "emotion_tone",
            "transition_note",
        }
    )

    @staticmethod
    def check(
        *,
        script: List[Dict[str, Any]],
        fact_checker_result: Dict[str, Any],
        structure_reviewer_result: Dict[str, Any],
        pending_tasks: List[Any],
        preferences_confirmed: bool,
    ) -> Dict[str, Any]:
        failed: List[str] = []
        passed: List[str] = []

        # 1. Script fields complete
        if not script:
            failed.append("script is empty")
        else:
            for i, seg in enumerate(script):
                missing = GateP2._REQUIRED_SEGMENT_FIELDS - set(seg.keys())
                if missing:
                    failed.append(
                        f"segment[{i}] {seg.get('segment_id', '?')} missing: {missing}"
                    )
            if not any("segment[" in f for f in failed):
                passed.append("script fields complete")

        # 2. FactChecker PASS
        if fact_checker_result.get("verdict") == "PASS":
            passed.append("FactChecker PASS")
        else:
            failed.append(
                f"FactChecker FAIL: {fact_checker_result.get('blocking_issues', [])}"
            )

        # 3. StructureReviewer PASS
        if structure_reviewer_result.get("verdict") == "PASS":
            passed.append("StructureReviewer PASS")
        else:
            failed.append(
                f"StructureReviewer FAIL: {structure_reviewer_result.get('blocking_issues', [])}"
            )

        # 4. No pending tasks
        if pending_tasks:
            failed.append(f"{len(pending_tasks)} pending tasks remain")
        else:
            passed.append("no pending tasks")

        # 5. Preferences confirmed
        if preferences_confirmed:
            passed.append("preferences confirmed")
        else:
            failed.append("preferences not confirmed")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }
