"""[SPEC-D-006 + SPEC-D-015] CrossPhaseAudit -- audit#1, #2, #3.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.7.7, SPEC-9.10.7, SPEC-9.11.6
"""

from __future__ import annotations

from typing import Any, Dict, List


class CrossPhaseAudit:
    """Cross-phase consistency audits #1, #2, #3."""

    # -- Audit #1 (P7) methods (D-006) --

    @staticmethod
    def audit_data_points(
        *, shots: List[Dict[str, Any]], script_data_points: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        dp_ids = {dp["data_point_id"] for dp in script_data_points}
        shot_refs: set[str] = set()
        for shot in shots:
            for ref in shot.get("data_point_refs", []):
                shot_refs.add(ref)
        unknown = shot_refs - dp_ids
        if unknown:
            return {
                "verdict": "FAIL",
                "detail": f"shot data_point_refs not in script: {unknown}",
            }
        return {"verdict": "PASS"}

    @staticmethod
    def audit_time_alignment(
        *, shots: List[Dict[str, Any]], timeline_segments: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        for shot in shots:
            tr = shot["time_range"]
            best_overlap = 0.0
            for seg in timeline_segments:
                overlap = max(
                    0.0,
                    min(tr["end_seconds"], seg["end_sec"])
                    - max(tr["start_seconds"], seg["start_sec"]),
                )
                shot_dur = tr["end_seconds"] - tr["start_seconds"]
                if shot_dur > 0:
                    best_overlap = max(best_overlap, overlap / shot_dur)
            if best_overlap < 0.80:
                return {
                    "verdict": "FAIL",
                    "detail": f"shot {shot.get('shot_id', '?')} overlap {best_overlap:.1%} < 80%",
                }
        return {"verdict": "PASS"}

    @staticmethod
    def run_audit_1(
        *,
        shots: List[Dict[str, Any]],
        script_data_points: List[Dict[str, Any]],
        timeline_segments: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        dp_result = CrossPhaseAudit.audit_data_points(
            shots=shots, script_data_points=script_data_points
        )
        time_result = CrossPhaseAudit.audit_time_alignment(
            shots=shots, timeline_segments=timeline_segments
        )
        inconsistencies: list[str] = []
        if dp_result["verdict"] == "FAIL":
            inconsistencies.append(dp_result.get("detail", "data point mismatch"))
        if time_result["verdict"] == "FAIL":
            inconsistencies.append(time_result.get("detail", "time misalignment"))
        return {
            "verdict": "PASS" if not inconsistencies else "FAIL",
            "inconsistency_count": len(inconsistencies),
            "inconsistencies": inconsistencies,
        }

    # -- Audit #2 (P10) methods (D-015) --

    @staticmethod
    def run_audit_2(
        *,
        subtitles: List[Dict[str, Any]],
        polished_script: Dict[str, Any],
        storyboard: List[Dict[str, Any]],
        rough_cut: Dict[str, Any],
        timeline: Dict[str, Any],
    ) -> Dict[str, Any]:
        inconsistencies: list[str] = []
        # Subtitle text check
        sub_text = " ".join(s.get("text", "") for s in subtitles)
        polished_text = " ".join(
            s.get("content", "") for s in polished_script.get("segments", [])
        )
        if sub_text != polished_text:
            inconsistencies.append("subtitle text mismatch")
        # Duration deviation <= 1s
        rc_dur = rough_cut.get("duration_seconds", 0)
        tl_dur = timeline.get("total_duration_sec", 0)
        if abs(rc_dur - tl_dur) > 1.0:
            inconsistencies.append(
                f"duration deviation {abs(rc_dur - tl_dur):.1f}s > 1s"
            )
        return {
            "verdict": "PASS" if not inconsistencies else "FAIL",
            "inconsistency_count": len(inconsistencies),
            "inconsistencies": inconsistencies,
        }

    # -- Audit #3 (P11) methods (D-015) --

    @staticmethod
    def run_audit_3(
        *,
        audit_1: Dict[str, Any],
        audit_2: Dict[str, Any],
    ) -> Dict[str, Any]:
        total = audit_1.get("inconsistency_count", 0) + audit_2.get(
            "inconsistency_count", 0
        )
        return {
            "verdict": "PASS" if total == 0 else "FAIL",
            "total_inconsistencies": total,
        }
