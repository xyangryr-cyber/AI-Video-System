"""[SPEC-D-004] P4 VoiceDirectionBridge -- P3 voice_direction -> TTS overrides.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.4.5

Pure code, 0 LLM tokens. Converts voice_direction sub-fields into
segment-level TTS parameter overrides deterministically.
"""

from __future__ import annotations

from typing import Any

# Emotion -> SSML emotion mapping
_EMOTION_MAP: dict[str, str] = {
    "excited": "excited",
    "neutral": "neutral",
    "calm": "calm",
    "serious": "serious",
    "urgent": "urgent",
    "whisper": "whisper",
}

# Pace -> rate multiplier mapping (5 levels)
_PACE_MAP: dict[str, float] = {
    "very_slow": 0.55,
    "slow": 0.8,
    "medium": 1.0,
    "fast": 1.25,
    "very_fast": 1.6,
}

# Energy -> volume multiplier mapping
_ENERGY_MAP: dict[str, float] = {
    "low": 0.8,
    "medium": 1.0,
    "high": 1.2,
}


class VoiceDirectionBridge:
    """Convert P3 voice_direction into TTS segment overrides.

    Pure function -- stateless, deterministic, no network/LLM calls.
    """

    @staticmethod
    def convert(vd: dict[str, Any]) -> dict[str, Any]:
        emotion = vd.get("emotion", "neutral")
        pace = vd.get("pace", "medium")
        energy = vd.get("energy", "medium")

        return {
            "emotion": _EMOTION_MAP.get(emotion, "neutral"),
            "rate_multiplier": _PACE_MAP.get(pace, 1.0),
            "volume": _ENERGY_MAP.get(energy, 1.0),
            "pause_after": vd.get("pause_after", 0.3),
        }
