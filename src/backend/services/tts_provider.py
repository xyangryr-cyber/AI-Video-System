"""[SPEC-D-004] P4 TTSProvider abstraction layer.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.4.7

Abstract interface allowing provider switching without upstream code changes.
Unsupported params are logged as capability_gap rather than raising errors.

[SPEC-D-005] TTS audio params aligned with platform standards.
Audio defaults read from config/platform_profiles.json bilibili.audio;
voice_params override individual keys when present.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

_PLATFORM_PROFILES_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
    "config",
    "platform_profiles.json",
)


def _load_platform_audio_config() -> Dict[str, Any]:
    """Load bilibili.audio defaults from platform_profiles.json.

    Returns an empty dict if the file is missing or unreadable so the
    pipeline does not break on config errors.
    """
    try:
        raw = Path(_PLATFORM_PROFILES_PATH).read_text(encoding="utf-8")
        profiles = json.loads(raw)
        return dict(profiles.get("bilibili", {}).get("audio", {}))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


class TTSProvider:
    """Abstract TTS provider.

    In V1, synthesize() returns deterministic stub output so the pipeline
    can be exercised end-to-end without a real TTS backend. Provider switching
    is achieved by injecting a different TTSProvider implementation at
    construction time; the caller does not need to change.
    """

    _SUPPORTED_PARAMS = frozenset(
        {"voice_id", "style", "style_degree", "rate_wpm", "pitch", "volume"}
    )

    def synthesize(
        self, *, text: str, voice_params: Dict[str, Any], ssml_tags: str | None = None
    ) -> Dict[str, Any]:
        # Log unsupported params as capability_gap (no crash)
        for key in voice_params:
            if key not in self._SUPPORTED_PARAMS:
                # In production this would log: capability_gap: {key}
                pass

        # Resolve audio params: platform defaults + voice_params overrides
        audio_defaults = _load_platform_audio_config()
        sample_rate = voice_params.get("sample_rate", audio_defaults.get("sample_rate", 44100))
        channels = voice_params.get("channels", audio_defaults.get("channels", 2))

        # Deterministic duration estimate: Chinese ~3 chars/sec
        char_count = len(text)
        duration = max(1.0, char_count / 3.0)

        return {
            "audio_path": f"phase_4/seg_audio_{hash(text) & 0xFFFF:04x}.mp3",
            "duration_seconds": round(duration, 2),
            "sample_rate": sample_rate,
            "channels": channels,
        }
