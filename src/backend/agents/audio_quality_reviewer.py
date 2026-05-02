"""[SPEC-D-004] P4 AudioQualityReviewer -- 7 quality criteria for TTS output.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.4.8

Placed outside reviewers/ package to avoid circular import (same pattern
as CompletenessReviewer / FactChecker).
"""

from __future__ import annotations

from typing import Any, Dict, List


class AudioQualityReviewer:
    """Review TTS audio quality across 7 criteria.

    Stateless -- each check is a pure function of metadata/parameters.
    In V1, checks operate on metadata rather than requiring actual audio
    files (file-level checks like "playable" are stubbed for CI).
    """

    CPS_MIN = 3.0
    CPS_MAX = 5.0
    SILENCE_MAX_SECONDS = 2.0
    TIMELINE_TOLERANCE_MS = 50  # 50ms
    GAP_MIN = 0.3
    GAP_MAX = 0.8
    DURATION_DEVIATION_MAX = 0.20  # 20%
    EXPECTED_SAMPLE_RATE = 44100

    @classmethod
    def review_segment_metadata(
        cls,
        *,
        word_count: int,
        duration_seconds: float,
        sample_rate: int,
        segment_id: str,
    ) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []

        # CPS check
        if duration_seconds > 0:
            cps = word_count / duration_seconds
            if cps < cls.CPS_MIN or cps > cls.CPS_MAX:
                checks.append(
                    {
                        "rule": "cps",
                        "verdict": "FAIL",
                        "detail": f"CPS {cps:.1f} not in [{cls.CPS_MIN}, {cls.CPS_MAX}]",
                    }
                )
            else:
                checks.append({"rule": "cps", "verdict": "PASS"})

        # Sample rate check
        checks.append(
            cls.check_sample_rate(sample_rate=sample_rate, segment_id=segment_id)
        )

        return {
            "segment_id": segment_id,
            "verdict": "FAIL"
            if any(c["verdict"] == "FAIL" for c in checks)
            else "PASS",
            "checks": checks,
        }

    @classmethod
    def check_silence(
        cls, *, silence_duration_seconds: float, segment_id: str
    ) -> Dict[str, Any]:
        if silence_duration_seconds > cls.SILENCE_MAX_SECONDS:
            return {
                "rule": "silence",
                "verdict": "FAIL",
                "detail": f"silence {silence_duration_seconds}s > {cls.SILENCE_MAX_SECONDS}s",
            }
        return {"rule": "silence", "verdict": "PASS"}

    @classmethod
    def check_timeline_accuracy(
        cls,
        *,
        timeline_duration: float,
        audio_duration: float,
        segment_id: str,
    ) -> Dict[str, Any]:
        diff_ms = abs(timeline_duration - audio_duration) * 1000
        if diff_ms > cls.TIMELINE_TOLERANCE_MS:
            return {
                "rule": "timeline_accuracy",
                "verdict": "FAIL",
                "detail": f"timeline vs audio diff {diff_ms:.0f}ms > {cls.TIMELINE_TOLERANCE_MS}ms",
            }
        return {"rule": "timeline_accuracy", "verdict": "PASS"}

    @classmethod
    def check_inter_segment_gap(
        cls, *, gap_seconds: float, segment_id: str
    ) -> Dict[str, Any]:
        if gap_seconds < cls.GAP_MIN or gap_seconds > cls.GAP_MAX:
            return {
                "rule": "inter_segment_gap",
                "verdict": "FAIL",
                "detail": f"gap {gap_seconds:.2f}s not in [{cls.GAP_MIN}, {cls.GAP_MAX}]",
            }
        return {"rule": "inter_segment_gap", "verdict": "PASS"}

    @classmethod
    def check_sample_rate(cls, *, sample_rate: int, segment_id: str) -> Dict[str, Any]:
        if sample_rate != cls.EXPECTED_SAMPLE_RATE:
            return {
                "rule": "sample_rate",
                "verdict": "FAIL",
                "detail": f"sample_rate {sample_rate} != {cls.EXPECTED_SAMPLE_RATE}",
            }
        return {"rule": "sample_rate", "verdict": "PASS"}
