"""[SPEC-D-006] P7 StoryboardReviewer -- L1 + L2 storyboard validation.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.7.5

Placed outside reviewers/ to avoid circular import.

v3.16 extension (SPEC-D-103): L1-A4 (anchor substring), L1-A5 (interval
continuity), L1-A6 (duration sum), L1-A7 (downstream_bindings).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.backend.services.shot_anchor_validator import ShotAnchorValidator


class StoryboardReviewer:
    """Review storyboard: L1 (time coverage, switch freq, duration, data coverage,
    time alignment, anchor validation) + L2 (narrative alignment, LLM-backed stub)."""

    SHOT_MIN_SECONDS = 3.0
    SHOT_MAX_SECONDS = 30.0
    OVERLAP_MIN = 0.80

    def __init__(self) -> None:
        self._anchor_validator = ShotAnchorValidator()

    @staticmethod
    def review_l1(
        shots: List[Dict[str, Any]],
        key_data_points: List[Dict[str, Any]] | None = None,
    ) -> Dict[str, Any]:
        blocking: list[str] = []

        # Time gaps
        for i in range(len(shots) - 1):
            end = shots[i]["time_range"]["end_seconds"]
            start = shots[i + 1]["time_range"]["start_seconds"]
            if start - end > 0.01:
                blocking.append(
                    f"time gap of {start - end:.2f}s between shot {i} and {i + 1}"
                )

        # Consecutive same type (3+)
        for i in range(len(shots) - 2):
            types = {shots[j]["type"] for j in range(i, i + 3)}
            if len(types) == 1:
                blocking.append(f"3+ consecutive {list(types)[0]} shots at index {i}")

        # Shot duration [3s, 30s]
        for shot in shots:
            dur = (
                shot["time_range"]["end_seconds"] - shot["time_range"]["start_seconds"]
            )
            if (
                dur < StoryboardReviewer.SHOT_MIN_SECONDS
                or dur > StoryboardReviewer.SHOT_MAX_SECONDS
            ):
                shot_id = shot.get("shot_id", "?")
                blocking.append(f"shot {shot_id} duration {dur:.1f}s out of range")

        # Data point coverage
        if key_data_points:
            dp_ids = {dp["data_point_id"] for dp in key_data_points}
            covered: set[str] = set()
            for shot in shots:
                for ref in shot.get("data_point_refs", []):
                    covered.add(ref)
            if dp_ids - covered:
                blocking.append(f"uncovered data points: {dp_ids - covered}")

        verdict = "FAIL" if blocking else "PASS"
        return {"verdict": verdict, "blocking_issues": blocking}

    # ------------------------------------------------------------------
    # L1-A4: anchor_text substring check (SPEC-D-103)
    # ------------------------------------------------------------------

    def check_l1_a4(
        self,
        *,
        polished_script: str,
        anchor_text: str,
    ) -> Dict[str, Any]:
        return self._anchor_validator.check_l1_a4_anchor_substring(
            polished_script=polished_script,
            anchor_text=anchor_text,
        )

    # ------------------------------------------------------------------
    # L1-A5: child shot interval continuity (SPEC-D-103)
    # ------------------------------------------------------------------

    def check_l1_a5(
        self,
        *,
        parent_text_len: int,
        child_shots: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return self._anchor_validator.check_l1_a5_intervals(
            parent_text_len=parent_text_len,
            child_shots=child_shots,
        )

    # ------------------------------------------------------------------
    # L1-A6: duration sum validation (SPEC-D-103)
    # ------------------------------------------------------------------

    def check_l1_a6(
        self,
        *,
        parent_duration: float,
        child_durations: List[float],
    ) -> Dict[str, Any]:
        return self._anchor_validator.check_l1_a6_duration_sum(
            parent_duration=parent_duration,
            child_durations=child_durations,
        )

    # ------------------------------------------------------------------
    # L1-A7: downstream_bindings reference validity (SPEC-D-103)
    # ------------------------------------------------------------------

    def check_l1_a7(
        self,
        *,
        downstream_bindings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        return self._anchor_validator.check_l1_a7_bindings(
            downstream_bindings=downstream_bindings,
        )

    # ------------------------------------------------------------------
    # Full L1 review with A4-A7 integration
    # ------------------------------------------------------------------

    def review_l1_extended(
        self,
        shots: List[Dict[str, Any]],
        *,
        polished_script: Optional[str] = None,
        key_data_points: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Full L1 review including v3.16 L1-A4 through L1-A7 checks.

        Returns aggregated verdict with per-rule results.
        """
        base_l1 = self.review_l1(shots, key_data_points)
        a4_results: List[Dict[str, Any]] = []
        a5_results: List[Dict[str, Any]] = []
        a6_results: List[Dict[str, Any]] = []
        a7_results: List[Dict[str, Any]] = []

        for shot in shots:
            # A4: check anchor against polished_script if present
            anchor_text = shot.get("anchor_text", "")
            if anchor_text and polished_script:
                a4_results.append(
                    self.check_l1_a4(
                        polished_script=polished_script, anchor_text=anchor_text
                    )
                )

            # A5: check child shot intervals if present
            child_shots = shot.get("child_shots")
            if child_shots:
                parent_text_len = shot.get("text_length") or len(
                    shot.get("narration_text", "")
                )
                a5_results.append(
                    self.check_l1_a5(
                        parent_text_len=parent_text_len,
                        child_shots=child_shots,
                    )
                )

            # A6: check duration sum if child shots present
            if child_shots:
                parent_dur = float(
                    shot["time_range"]["end_seconds"]
                    - shot["time_range"]["start_seconds"]
                )
                child_durs = [
                    float(cs.get("time_range", {}).get("end_seconds", 0))
                    - float(cs.get("time_range", {}).get("start_seconds", 0))
                    for cs in child_shots
                ]
                a6_results.append(
                    self.check_l1_a6(
                        parent_duration=parent_dur,
                        child_durations=child_durs,
                    )
                )

            # A7: check downstream_bindings if present
            bindings = shot.get("downstream_bindings")
            if bindings:
                a7_results.append(self.check_l1_a7(downstream_bindings=bindings))

        # Aggregate verdict
        all_checks = a4_results + a5_results + a6_results + a7_results
        all_pass = base_l1["verdict"] == "PASS" and all(
            r.get("passed", True) for r in all_checks
        )

        return {
            "verdict": "PASS" if all_pass else "FAIL",
            "base_l1": base_l1,
            "l1_a4_anchor": a4_results,
            "l1_a5_intervals": a5_results,
            "l1_a6_duration": a6_results,
            "l1_a7_bindings": a7_results,
        }

    @classmethod
    def review(cls, shots: List[Dict[str, Any]]) -> Dict[str, Any]:
        l1 = cls.review_l1(shots)
        l2_called = False
        if l1["verdict"] == "PASS":
            l2_called = True
        return {"verdict": l1["verdict"], "l1_result": l1, "l2_called": l2_called}
