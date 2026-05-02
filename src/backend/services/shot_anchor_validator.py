"""[SPEC-D-103] ShotAnchorValidator -- L1-A4..A7 shot anchor validation.

Authority: docs/specs/SPEC-D-pipeline-phases.md §D-BDD-4

Provides programmatic (0-token) validations for shot splitting:
- L1-A4: anchor_text must be an exact substring of polished_script
- L1-A5: child shot character intervals must have no overlap and no gaps
- L1-A6: child shot duration sum must equal parent duration within 100ms
- L1-A7: downstream_bindings must reference valid phases (P8/P9/P10)
"""

from __future__ import annotations

from typing import Any, Dict, List


class ShotAnchorValidator:
    """Validates shot anchor text, intervals, durations, and downstream bindings."""

    TOLERANCE_SECONDS = 0.1  # 100ms
    VALID_BINDING_PHASES = frozenset({"P8", "P9", "P10"})

    # -- L1-A4: anchor text substring check -----------------------------------

    def check_l1_a4_anchor_substring(
        self,
        *,
        polished_script: str,
        anchor_text: str,
    ) -> Dict[str, Any]:
        """L1-A4: verify anchor_text is an exact substring of polished_script.

        Returns dict with ``passed`` (bool), ``rule`` (str).
        """
        passed = anchor_text in polished_script
        return {
            "rule": "L1-A4",
            "passed": passed,
            "anchor_text": anchor_text,
            "polished_script_snippet": polished_script[:200],
            "detail": (
                "anchor_text found in polished_script"
                if passed
                else "anchor_text NOT found in polished_script"
            ),
        }

    # -- L1-A5: child shot interval coverage ---------------------------------

    def check_l1_a5_intervals(
        self,
        *,
        parent_text_len: int,
        child_shots: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """L1-A5: verify child shot intervals have no overlap and no gaps.

        Each child_shot dict must contain ``char_start`` and ``char_end``
        (exclusive end, matching Python slice semantics). Intervals must
        partition [0, parent_text_len) without overlap or gap.
        """
        if not child_shots:
            return {
                "rule": "L1-A5",
                "passed": parent_text_len == 0,
                "detail": "no child shots to validate",
            }

        # Sort by char_start
        sorted_shots = sorted(child_shots, key=lambda s: s["char_start"])

        # Check start at 0
        if sorted_shots[0]["char_start"] != 0:
            return {
                "rule": "L1-A5",
                "passed": False,
                "detail": f"first interval does not start at 0 (starts at {sorted_shots[0]['char_start']})",
            }

        # Check no overlap, no gap
        prev_end = 0
        for shot in sorted_shots:
            start = shot["char_start"]
            end = shot["char_end"]

            if start < prev_end:
                return {
                    "rule": "L1-A5",
                    "passed": False,
                    "detail": f"overlap detected: shot {shot['shot_id']} starts at {start} but previous ends at {prev_end}",
                }
            if start > prev_end:
                return {
                    "rule": "L1-A5",
                    "passed": False,
                    "detail": f"gap detected: expected start at {prev_end} but shot {shot['shot_id']} starts at {start}",
                }
            prev_end = end

        # Check end matches parent length
        if prev_end != parent_text_len:
            return {
                "rule": "L1-A5",
                "passed": False,
                "detail": f"last interval ends at {prev_end} but parent text length is {parent_text_len}",
            }

        return {
            "rule": "L1-A5",
            "passed": True,
            "detail": "all intervals non-overlapping and fully covering parent text",
        }

    # -- L1-A6: duration sum check --------------------------------------------

    def check_l1_a6_duration_sum(
        self,
        *,
        parent_duration: float,
        child_durations: List[float],
    ) -> Dict[str, Any]:
        """L1-A6: verify sum of child durations equals parent duration within 100ms.

        Args:
            parent_duration: parent shot duration in seconds.
            child_durations: list of child shot durations in seconds.
        """
        child_sum = sum(child_durations)
        diff = abs(child_sum - parent_duration)
        passed = diff <= self.TOLERANCE_SECONDS

        return {
            "rule": "L1-A6",
            "passed": passed,
            "parent_duration": parent_duration,
            "child_sum": child_sum,
            "sum_difference": round(diff, 6),
            "tolerance_seconds": self.TOLERANCE_SECONDS,
            "detail": (
                f"child durations sum ({child_sum}s) matches parent ({parent_duration}s) within {self.TOLERANCE_SECONDS}s"
                if passed
                else f"child durations sum ({child_sum}s) differs from parent ({parent_duration}s) by {diff:.3f}s (> {self.TOLERANCE_SECONDS}s)"
            ),
        }

    # -- L1-A7: downstream bindings validity ----------------------------------

    def check_l1_a7_bindings(
        self,
        *,
        downstream_bindings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """L1-A7: verify downstream_bindings reference valid phases (P8/P9/P10).

        Each binding dict must have a ``phase`` key whose value is one of
        P8, P9, P10.
        """
        invalid_bindings: List[Dict[str, Any]] = []

        for binding in downstream_bindings:
            phase = binding.get("phase", "")
            if phase not in self.VALID_BINDING_PHASES:
                invalid_bindings.append(binding)

        passed = len(invalid_bindings) == 0

        return {
            "rule": "L1-A7",
            "passed": passed,
            "total_bindings": len(downstream_bindings),
            "invalid_bindings": invalid_bindings,
            "valid_phases": sorted(self.VALID_BINDING_PHASES),
            "detail": (
                "all downstream_bindings reference valid phases"
                if passed
                else f"{len(invalid_bindings)} binding(s) reference invalid phases: "
                f"{[b.get('phase') for b in invalid_bindings]}"
            ),
        }


__all__ = ["ShotAnchorValidator"]
