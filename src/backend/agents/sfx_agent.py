"""[SPEC-D-005] P6 SFXAgent -- functional + semantic SFX production.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.6
"""

from __future__ import annotations

from typing import Any, Dict, List

# Dual type mapping: functional -> semantic
_TYPE_MAPPING: Dict[str, str] = {
    "boom": "reveal",
    "whoosh": "contrast",
    "ding": "rise_positive",
    "rise": "rise_positive",
    "warm_pad": "drop_negative",
}

# Built-in SFX library (stub)
_BUILTIN_SFX: Dict[str, List[Dict[str, Any]]] = {
    "boom": [{"file_path": "builtin/boom_001.wav"}],
    "whoosh": [{"file_path": "builtin/whoosh_001.wav"}],
    "ding": [{"file_path": "builtin/ding_001.wav"}],
    "rise": [{"file_path": "builtin/rise_001.wav"}],
    "warm_pad": [{"file_path": "builtin/warm_pad_001.wav"}],
}


class SFXAgent:
    """P6 SFX producer with dual type system and constraint checks."""

    @staticmethod
    def get_type_mapping() -> Dict[str, str]:
        return dict(_TYPE_MAPPING)

    # -- SFX production (AC-8) --

    @staticmethod
    def produce_sfx(*, timeline: Dict[str, Any]) -> List[Dict[str, Any]]:
        segments = timeline.get("segments", [])
        sfx_list: List[Dict[str, Any]] = []
        types = list(_TYPE_MAPPING.keys())

        for i, seg in enumerate(segments):
            if i % 2 == 0:
                continue  # Not every segment gets SFX

            sfx_type = types[i % len(types)]
            semantic = _TYPE_MAPPING.get(sfx_type, "unknown")
            timestamp = seg.get("start_sec", 0.0) + 1.0

            sfx_list.append(
                {
                    "sfx_id": f"sfx_{i:03d}",
                    "type": sfx_type,
                    "semantic_type": semantic,
                    "timestamp_seconds": round(timestamp, 2),
                    "trigger_text": seg.get("content", "")[:20],
                    "reason": f"emphasize {semantic} at segment {seg['segment_id']}",
                    "volume_db": -18.0,
                    "duration_seconds": 1.0,
                    "file_path": f"phase_6/sfx_{i:03d}.wav",
                }
            )
        return sfx_list

    # -- Sparsity check (AC-9) --

    @staticmethod
    def check_sparsity(
        sfx_list: List[Dict[str, Any]], min_interval: float = 15.0
    ) -> Dict[str, Any]:
        if len(sfx_list) < 2:
            return {"verdict": "PASS", "rule": "sparsity"}

        timestamps = sorted(s["timestamp_seconds"] for s in sfx_list)
        gaps = [timestamps[i + 1] - timestamps[i] for i in range(len(timestamps) - 1)]
        avg_gap = sum(gaps) / len(gaps) if gaps else float("inf")

        if avg_gap < min_interval:
            return {
                "verdict": "FAIL",
                "rule": "sparsity",
                "detail": f"average gap {avg_gap:.1f}s < {min_interval}s minimum",
            }
        return {"verdict": "PASS", "rule": "sparsity"}

    # -- Type diversity (AC-9) --

    @staticmethod
    def check_type_diversity(
        sfx_list: List[Dict[str, Any]], min_types: int = 3
    ) -> Dict[str, Any]:
        unique_types = {s["type"] for s in sfx_list}
        if len(unique_types) < min_types:
            return {
                "verdict": "FAIL",
                "rule": "type_diversity",
                "detail": f"{len(unique_types)} types < {min_types} required",
            }
        return {"verdict": "PASS", "rule": "type_diversity"}

    # -- BGM overlap check (AC-9) --

    @staticmethod
    def check_bgm_overlap(
        *,
        sfx_list: List[Dict[str, Any]],
        bgm_transition_timestamps: List[float],
        tolerance: float = 2.0,
    ) -> Dict[str, Any]:
        for sfx in sfx_list:
            ts = sfx["timestamp_seconds"]
            for bt in bgm_transition_timestamps:
                if abs(ts - bt) <= tolerance:
                    return {
                        "verdict": "FAIL",
                        "rule": "bgm_overlap",
                        "detail": f"SFX at {ts}s too close to BGM transition at {bt}s",
                    }
        return {"verdict": "PASS", "rule": "bgm_overlap"}

    # -- 3-level fallback (AC-10) --

    @staticmethod
    def fetch_sfx(*, source: str, sfx_type: str) -> Dict[str, Any]:
        # 3-level fallback: builtin -> Freesound -> user upload
        if sfx_type in _BUILTIN_SFX:
            return {
                "file_path": _BUILTIN_SFX[sfx_type][0]["file_path"],
                "source": "builtin",
            }
        # Freesound stub
        return {
            "file_path": f"freesound/{sfx_type}_001.wav",
            "fallback_used": True,
            "source_attempted": source,
            "reason_failed": "builtin not found, using freesound stub",
            "source_used": "freesound",
        }
