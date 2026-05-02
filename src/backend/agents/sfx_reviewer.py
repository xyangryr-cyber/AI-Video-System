"""[SPEC-D-005] P6 SFXReviewer -- pure L1 (0 token) SFX quality review.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.6.5

Placed outside reviewers/ to avoid circular import.
"""

from __future__ import annotations

from typing import Any, Dict, List

_CONSECUTIVE_FAIL_THRESHOLD = 3
_SFX_NARRATION_MARGIN_DB = 6  # SFX+BGM combined <= narration -6dB


class SFXReviewer:
    """Pure L1 SFX reviewer: density, type diversity, voice masking, BGM overlap,
    file completeness. 0 LLM tokens."""

    @staticmethod
    def should_suggest_skip(consecutive_fails: int) -> bool:
        return consecutive_fails >= _CONSECUTIVE_FAIL_THRESHOLD

    @staticmethod
    def review(
        *, sfx_list: List[Dict[str, Any]], narration_volume_db: float
    ) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []

        # 1. Density: average interval >= 15s
        checks.append(SFXReviewer._check_density(sfx_list))

        # 2. Type diversity: >= 3 different types
        checks.append(SFXReviewer._check_diversity(sfx_list))

        # 3. Voice masking: SFX volume <= narration -6dB
        checks.append(SFXReviewer._check_voice_masking(sfx_list, narration_volume_db))

        # 4. BGM overlap (delegated to caller, here just file completeness)
        checks.append(SFXReviewer._check_file_completeness(sfx_list))

        verdict = "FAIL" if any(c["verdict"] == "FAIL" for c in checks) else "PASS"
        return {"verdict": verdict, "checks": checks}

    @staticmethod
    def _check_density(sfx_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        if len(sfx_list) < 2:
            return {"rule": "density", "verdict": "PASS"}

        timestamps = sorted(s["timestamp_seconds"] for s in sfx_list)
        gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        avg_gap = sum(gaps) / len(gaps)

        if avg_gap < 15.0:
            return {
                "rule": "density",
                "verdict": "FAIL",
                "detail": f"average interval {avg_gap:.1f}s < 15s minimum",
            }
        return {"rule": "density", "verdict": "PASS"}

    @staticmethod
    def _check_diversity(sfx_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        unique_types = {s.get("type") for s in sfx_list}
        if len(unique_types) < 3:
            return {
                "rule": "diversity",
                "verdict": "FAIL",
                "detail": f"{len(unique_types)} types < 3 required",
            }
        return {"rule": "diversity", "verdict": "PASS"}

    @staticmethod
    def _check_voice_masking(
        sfx_list: List[Dict[str, Any]], narration_volume_db: float
    ) -> Dict[str, Any]:
        max_allowed = narration_volume_db - _SFX_NARRATION_MARGIN_DB
        for sfx in sfx_list:
            vol = sfx.get("volume_db", 0)
            if vol > max_allowed:
                return {
                    "rule": "voice_masking",
                    "verdict": "FAIL",
                    "detail": f"SFX {sfx['sfx_id']} at {vol}dB exceeds max {max_allowed}dB",
                }
        return {"rule": "voice_masking", "verdict": "PASS"}

    @staticmethod
    def _check_file_completeness(sfx_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        for sfx in sfx_list:
            if not sfx.get("file_path"):
                return {
                    "rule": "file_completeness",
                    "verdict": "FAIL",
                    "detail": f"SFX {sfx.get('sfx_id', '?')} missing file_path",
                }
        return {"rule": "file_completeness", "verdict": "PASS"}
