"""[SPEC-D-006] P7 StoryboardAgent -- shot planning, style lock, data viz.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.7
"""

from __future__ import annotations

from typing import Any

_DARK_SCHEMES = [
    {
        "scheme_id": "dark_professional",
        "colors": {"bg": "#1a1a2e", "fg": "#e0e0e0", "accent": "#00d4ff"},
    },
    {
        "scheme_id": "dark_warm",
        "colors": {"bg": "#1e1e1e", "fg": "#f5f5f5", "accent": "#ff6b35"},
    },
    {
        "scheme_id": "dark_cool",
        "colors": {"bg": "#0d1117", "fg": "#c9d1d9", "accent": "#58a6ff"},
    },
]

_LIGHT_SCHEMES = [
    {
        "scheme_id": "light_clean",
        "colors": {"bg": "#ffffff", "fg": "#333333", "accent": "#2563eb"},
    },
    {
        "scheme_id": "light_warm",
        "colors": {"bg": "#fafaf9", "fg": "#44403c", "accent": "#ea580c"},
    },
    {
        "scheme_id": "light_cool",
        "colors": {"bg": "#f8fafc", "fg": "#334155", "accent": "#0891b2"},
    },
]


class StoryboardAgent:
    """P7 Storyboard producer: shot planning, style lock, data viz coverage."""

    @staticmethod
    def produce_storyboard(
        *,
        timeline: dict[str, Any],
        script: list[dict[str, Any]],
        measured_duration_sec: float | None = None,
    ) -> list[dict[str, Any]]:
        segments = timeline.get("segments", [])
        num_segments = len(segments)
        shots: list[dict[str, Any]] = []

        # If measured_duration_sec is available, redistribute time evenly
        if measured_duration_sec is not None and num_segments > 0:
            per_seg = measured_duration_sec / num_segments
            for i, seg in enumerate(segments):
                start = round(i * per_seg, 2)
                end = round((i + 1) * per_seg, 2)
                _seg_id = seg["segment_id"]
                shot_type = "template" if i % 2 == 0 else "broll"
                data_refs = (
                    [dp["data_point_id"] for dp in script[i].get("key_data_points", [])]
                    if i < len(script)
                    else []
                )
                shots.append(
                    {
                        "shot_id": f"shot_{i:03d}",
                        "time_range": {"start_seconds": start, "end_seconds": end},
                        "type": shot_type,
                        "template_type": "chart_card" if shot_type == "template" else None,
                        "search_keywords": [seg.get("emotion_tone", "neutral")],
                        "content": seg.get("content", ""),
                        "narration_text": seg.get("content", ""),
                        "data_point_refs": data_refs,
                    }
                )
            return shots

        for i, seg in enumerate(segments):
            start = seg["start_sec"]
            end = seg["end_sec"]
            _seg_id = seg["segment_id"]

            shot_type = "template" if i % 2 == 0 else "broll"
            data_refs = (
                [dp["data_point_id"] for dp in script[i].get("key_data_points", [])]
                if i < len(script)
                else []
            )

            shots.append(
                {
                    "shot_id": f"shot_{i:03d}",
                    "time_range": {"start_seconds": start, "end_seconds": end},
                    "type": shot_type,
                    "template_type": "chart_card" if shot_type == "template" else None,
                    "search_keywords": [seg.get("emotion_tone", "neutral")],
                    "content": seg.get("content", ""),
                    "narration_text": seg.get("content", ""),
                    "data_point_refs": data_refs,
                }
            )
        return shots

    @staticmethod
    def check_data_coverage(
        *, shots: list[dict[str, Any]], key_data_points: list[dict[str, Any]]
    ) -> dict[str, Any]:
        all_dp_ids = {dp["data_point_id"] for dp in key_data_points}
        covered: set[str] = set()
        for shot in shots:
            for ref in shot.get("data_point_refs", []):
                covered.add(ref)
        if not all_dp_ids:
            return {"coverage_ratio": 1.0, "verdict": "PASS"}
        ratio = len(covered & all_dp_ids) / len(all_dp_ids)
        return {
            "coverage_ratio": round(ratio, 3),
            "verdict": "PASS" if ratio >= 0.8 else "FAIL",
        }

    @staticmethod
    def generate_style_candidates(
        *, count: int = 3, visual_preferences: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        palette = (visual_preferences or {}).get("preferred_palette", "")
        source = _DARK_SCHEMES if "dark" in palette.lower() else _LIGHT_SCHEMES
        return list(source[:count])

    @staticmethod
    def confirm_style_lock(*, scheme_id: str) -> dict[str, Any]:
        return {
            "style_lock_path": f"phase_7/style_lock_{scheme_id}.json",
            "confirmed": True,
            "scheme_id": scheme_id,
        }

    @staticmethod
    def check_consecutive_same_type(shots: list[dict[str, Any]]) -> dict[str, Any]:
        if len(shots) < 3:
            return {"verdict": "PASS", "rule": "consecutive_same_type"}
        for i in range(len(shots) - 2):
            types = {shots[j]["type"] for j in range(i, i + 3)}
            if len(types) == 1:
                return {
                    "verdict": "FAIL",
                    "rule": "consecutive_same_type",
                    "detail": f"3 consecutive {list(types)[0]} shots at index {i}",
                }
        return {"verdict": "PASS", "rule": "consecutive_same_type"}

    @staticmethod
    def check_scene_switch(
        *, shots: list[dict[str, Any]], window_seconds: float = 30.0
    ) -> dict[str, Any]:
        # Every 30s window must have at least 1 scene/type switch
        if not shots:
            return {"verdict": "PASS", "rule": "scene_switch"}
        max_time = max(s["time_range"]["end_seconds"] for s in shots)
        window_start = 0.0
        while window_start + window_seconds <= max_time:
            window_end = window_start + window_seconds
            types_in_window: set[str] = set()
            shot_count = 0
            for s in shots:
                if (
                    s["time_range"]["start_seconds"] < window_end
                    and s["time_range"]["end_seconds"] > window_start
                ):
                    types_in_window.add(s["type"])
                    shot_count += 1
            if shot_count >= 2 and len(types_in_window) < 2:
                return {
                    "verdict": "FAIL",
                    "rule": "scene_switch",
                    "detail": f"window [{window_start}, {window_end}] has only {types_in_window}",
                }
            window_start += window_seconds
        return {"verdict": "PASS", "rule": "scene_switch"}
