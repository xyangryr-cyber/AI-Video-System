"""[SPEC-D-002] P1 StructureReviewer -- validates outline structure.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.1.x
"""

from __future__ import annotations

from typing import Any, Dict, List


class StructureReviewer:
    """Validate outline: structure, duration ratios, inter-version diversity."""

    def review(
        self,
        outlines: List[Dict[str, Any]],
        *,
        selected_version_id: str | None = None,
    ) -> Dict[str, Any]:
        notes: list[str] = []
        blocking: list[str] = []

        if selected_version_id:
            selected = _find_version(outlines, selected_version_id)
            if selected is None:
                return {
                    "verdict": "FAIL",
                    "notes": [],
                    "blocking_issues": [
                        f"Selected version {selected_version_id!r} not found"
                    ],
                }
            # Check opening + body(>=2) + closing
            beats = selected.get("narrative_beats", [])
            if len(beats) < 4:
                blocking.append(f"Need at least 4 beats, got {len(beats)}")

            if beats:
                beat_types = [b["type"] for b in beats]
                if beat_types[0] != "hook":
                    blocking.append("First beat must be 'hook'")
                if beat_types[-1] != "conclusion":
                    blocking.append("Last beat must be 'conclusion'")
                body_beats = beat_types[1:-1]
                if len(body_beats) < 2:
                    blocking.append(f"Body needs >= 2 beats, got {len(body_beats)}")

            # Duration ratio sum ~= 1.0
            total_dur = beats[-1]["end_seconds"] if beats else 1
            ratio_sum = sum(
                (b["end_seconds"] - b["start_seconds"]) / total_dur for b in beats
            )
            if abs(ratio_sum - 1.0) > 0.05:
                blocking.append(
                    f"duration_ratio sum {ratio_sum:.3f} not in [0.95, 1.05]"
                )

            # transition_to_next non-empty for all except last beat
            for b in beats[:-1]:
                if not b.get("transition_to_next"):
                    blocking.append(f"Beat '{b['type']}' missing transition_to_next")

        # Inter-version diversity (at least 1 of 3: different viewpoint,
        # different beat structure, different supporting data)
        if len(outlines) >= 2:
            v0, v1 = outlines[0], outlines[1]
            diverse = (
                v0.get("viewpoint") != v1.get("viewpoint")
                or _beat_duration_differs(v0, v1)
                or _supporting_data_differs(v0, v1)
            )
            if diverse:
                notes.append("inter-version diversity OK")
            else:
                blocking.append("No inter-version diversity")

        verdict = "FAIL" if blocking else "PASS"
        if verdict == "PASS":
            notes.append("StructureReviewer PASS")

        return {
            "verdict": verdict,
            "notes": notes,
            "blocking_issues": blocking,
        }


def _find_version(
    outlines: List[Dict[str, Any]], version_id: str
) -> Dict[str, Any] | None:
    for o in outlines:
        if o.get("version_id") == version_id:
            return o
    return None


def _beat_duration_differs(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    a_beats = a.get("narrative_beats", [])
    b_beats = b.get("narrative_beats", [])
    if len(a_beats) != len(b_beats):
        return True
    for ba, bb in zip(a_beats, b_beats):
        if (ba["end_seconds"] - ba["start_seconds"]) != (
            bb["end_seconds"] - bb["start_seconds"]
        ):
            return True
    return False


def _supporting_data_differs(a: Dict[str, Any], b: Dict[str, Any]) -> bool:
    a_data = [
        d
        for beat in a.get("narrative_beats", [])
        for d in beat.get("supporting_data", [])
    ]
    b_data = [
        d
        for beat in b.get("narrative_beats", [])
        for d in beat.get("supporting_data", [])
    ]
    return a_data != b_data
