"""[SPEC-D-005] P5 BGMAgent -- emotion curve, BGM selection, volume envelope.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.5
"""

from __future__ import annotations

from typing import Any

# Emotion -> energy mapping
_EMOTION_ENERGY: dict[str, int] = {
    "excited": 8,
    "neutral": 5,
    "calm": 3,
    "serious": 6,
}

# Local BGM library (stub)
_LOCAL_LIBRARY: list[dict[str, Any]] = [
    {"track_id": "local_upbeat_01", "energy_score": 8, "source": "local_library"},
    {"track_id": "local_neutral_01", "energy_score": 5, "source": "local_library"},
    {"track_id": "local_calm_01", "energy_score": 3, "source": "local_library"},
    {"track_id": "local_dramatic_01", "energy_score": 7, "source": "local_library"},
]

_COPYRIGHT_MAP: dict[str, str] = {
    "mubert": "proprietary",
    "local_library": "CC0",
    "freesound": "CC-BY",
}


class BGMAgent:
    """P5 BGM producer: emotion curve, candidate selection, volume envelope."""

    # -- Emotion curve (AC-1) --

    @staticmethod
    def produce_emotion_curve(*, timeline: dict[str, Any]) -> dict[str, Any]:
        segments_out: list[dict[str, Any]] = []
        for seg in timeline.get("segments", []):
            emotion_raw = seg.get("emotion_tone", "neutral")
            emotion = emotion_raw if emotion_raw in _EMOTION_ENERGY else "neutral"
            energy = _EMOTION_ENERGY.get(emotion, 5)
            segments_out.append(
                {
                    "segment_id": seg["segment_id"],
                    "emotion": emotion,
                    "energy": energy,
                }
            )
        # Mark transition points
        transitions: list[float] = []
        for seg in timeline.get("segments", []):
            transitions.append(seg.get("start_sec", 0.0))

        return {"segments": segments_out, "transition_points": transitions}

    # -- BGM candidates (AC-2) --

    @staticmethod
    def select_bgm_candidates(
        *, emotion_curve: dict[str, Any], count: int = 3
    ) -> list[dict[str, Any]]:
        segments = emotion_curve.get("segments", [])
        if not segments:
            return _LOCAL_LIBRARY[:count]

        # Average energy across the curve
        avg_energy = sum(s.get("energy", 5) for s in segments) / len(segments)
        # Sort library by proximity to avg energy
        scored = sorted(
            _LOCAL_LIBRARY,
            key=lambda t: abs(t["energy_score"] - avg_energy),
        )
        candidates: list[dict[str, Any]] = []
        for t in scored[:count]:
            candidates.append(
                {
                    "track_id": t["track_id"],
                    "energy_score": t["energy_score"],
                    "source": t["source"],
                }
            )
        return candidates

    # -- Volume envelope (AC-3) --

    @staticmethod
    def design_volume_envelope(*, segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
        # Hook <= -12dB, body <= -20dB, transition <= -14dB
        _TYPE_DEFAULTS: dict[str, float] = {
            "hook": -12.0,
            "body": -20.0,
            "transition": -14.0,
        }
        envelope: list[dict[str, Any]] = []
        for seg in segments:
            seg_type = seg.get("type", "body")
            volume_db = _TYPE_DEFAULTS.get(seg_type, -20.0)
            envelope.append(
                {
                    "type": seg_type,
                    "start_sec": seg.get("start_sec", 0.0),
                    "volume_db": volume_db,
                }
            )
        return envelope

    # -- Fallback (AC-4) --

    @staticmethod
    def fetch_bgm_track(*, source: str, emotion: str, energy: int) -> dict[str, Any]:
        # 2-level fallback: Mubert API -> local library
        if source == "mubert_api":
            # Stub: Mubert unavailable, fallback to local
            local = _LOCAL_LIBRARY[0]
            return {
                "track_id": local["track_id"],
                "fallback_used": True,
                "source_attempted": "mubert_api",
                "reason_failed": "API unavailable (stub)",
                "source_used": "local_library",
            }
        # Direct from local library
        for t in _LOCAL_LIBRARY:
            if abs(t["energy_score"] - energy) <= 2:
                return {"track_id": t["track_id"], "source": t["source"]}
        return {"track_id": _LOCAL_LIBRARY[0]["track_id"], "source": "local_library"}

    # -- Copyright marking (AC-5) --

    @staticmethod
    def mark_copyright(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for c in candidates:
            source = c.get("source", "")
            copyright_tag = _COPYRIGHT_MAP.get(source, "proprietary")
            result.append({**c, "copyright": copyright_tag})
        return result
