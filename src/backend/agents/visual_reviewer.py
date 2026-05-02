"""[SPEC-D-007] P8 VisualReviewer -- pure L1 visual quality checks.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.8.5
"""

from __future__ import annotations

from typing import Any, Dict, List


class VisualReviewer:
    """Pure L1 visual review: render completeness, number cross-check, provenance."""

    @staticmethod
    def review(rendered_shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []
        for shot in rendered_shots:
            if not shot.get("render_path"):
                checks.append(
                    {
                        "rule": "render_path",
                        "shot_id": shot.get("shot_id", "?"),
                        "verdict": "FAIL",
                        "detail": "missing render_path",
                    }
                )
            else:
                checks.append(
                    {
                        "rule": "render_path",
                        "shot_id": shot["shot_id"],
                        "verdict": "PASS",
                    }
                )
        verdict = "FAIL" if any(c["verdict"] == "FAIL" for c in checks) else "PASS"
        return {"verdict": verdict, "checks": checks}

    @staticmethod
    def check_number_match(
        *, oral_numbers: List[str], visual_numbers: List[str]
    ) -> Dict[str, Any]:
        oral_set = set(oral_numbers)
        visual_set = set(visual_numbers)
        if oral_set != visual_set:
            return {
                "verdict": "FAIL",
                "detail": f"oral={oral_set - visual_set} visual={visual_set - oral_set}",
            }
        return {"verdict": "PASS"}

    @staticmethod
    def audit_data_provenance(
        *, chart_data_points: List[str], source_data_points: List[str]
    ) -> Dict[str, Any]:
        missing = set(chart_data_points) - set(source_data_points)
        if missing:
            return {"verdict": "FAIL", "detail": f"no source for: {missing}"}
        return {"verdict": "PASS"}
