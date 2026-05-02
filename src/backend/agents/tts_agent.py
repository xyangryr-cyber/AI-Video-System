"""[SPEC-D-004] P4 TTSAgent -- voice selection, TTS synthesis, timeline production.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.4

8 capabilities: preferred voice priority, new voice confirmation, global voice
params, segment overrides, voice direction bridging, digit-aware slowdown,
TTSProvider abstraction, timeline.json production.
"""

from __future__ import annotations

from typing import Any, Dict, List

from src.backend.services.bytedance_tts_provider import ByteDanceTTSProvider
from src.backend.services.digit_slowdown import DigitSlowdown
from src.backend.services.tts_provider import TTSProvider
from src.backend.services.voice_direction_bridge import VoiceDirectionBridge

_DEFAULT_VOICES = [
    {"voice_id": "voice_zh_female_01", "gender": "female", "style": "news"},
    {"voice_id": "voice_zh_male_01", "gender": "male", "style": "news"},
    {"voice_id": "voice_zh_female_02", "gender": "female", "style": "casual"},
]


class TTSAgent:
    """P4 TTS producer with voice selection, synthesis, and timeline output.

    Stateless -- all state comes from arguments. Provider injection via
    constructor enables switching without caller changes.
    """

    def __init__(self, provider: TTSProvider | None = None) -> None:
        self._provider = provider or ByteDanceTTSProvider()
        self._bridge = VoiceDirectionBridge()
        self._slowdown = DigitSlowdown()

    # -- Voice candidate selection (AC-1, AC-2) --

    @staticmethod
    def select_voice_candidates(
        *,
        polished_script: Dict[str, Any],
        voice_preferences: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        preferred_id = None
        if voice_preferences:
            preferred_id = voice_preferences.get("preferred_voice_id")

        candidates: List[Dict[str, Any]] = []
        if preferred_id:
            # Put preferred voice first with is_recommended=True
            candidates.append(
                {"voice_id": preferred_id, "is_recommended": True, "why": "preferred"}
            )
            # Add 1-2 recommended alternatives
            for v in _DEFAULT_VOICES:
                if v["voice_id"] != preferred_id and len(candidates) < 3:
                    candidates.append({**v, "is_recommended": False})
        else:
            # No preference: generate 2-3 candidates
            for v in _DEFAULT_VOICES[:3]:
                candidates.append({**v, "is_recommended": False})

        return candidates

    # -- Voice confirmation (AC-3) --

    @staticmethod
    def confirm_voice_selection(
        *,
        selected_voice_id: str,
        preferred_voice_id: str,
        user_accepted: bool,
    ) -> Dict[str, Any]:
        if selected_voice_id == preferred_voice_id:
            return {"write_target": "none", "voice_id": selected_voice_id}
        target = "user_preferences_md" if user_accepted else "project_preferences_md"
        return {"write_target": target, "voice_id": selected_voice_id}

    # -- Global voice params (AC-4) --

    @staticmethod
    def build_global_voice_params(*, voice_id: str) -> Dict[str, Any]:
        return {
            "voice_id": voice_id,
            "style": "news",
            "style_degree": 0.5,
            "rate_wpm": 160,
            "pitch": 0.0,
            "volume": 1.0,
        }

    # -- Segment overrides (AC-5) --

    @staticmethod
    def build_segment_overrides(
        *,
        segment: Dict[str, Any],
        digit_slowdown: bool = False,
        global_voice_params: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        overrides: Dict[str, Any] = {}
        vd = segment.get("voice_direction")
        if vd:
            vd_result = VoiceDirectionBridge.convert(vd)
            overrides.update(vd_result)

        if digit_slowdown:
            overrides["rate_multiplier"] = overrides.get("rate_multiplier", 1.0) * 0.7

        return overrides

    # -- Timeline production (AC-9) --

    def build_timeline(
        self,
        *,
        polished_script: Dict[str, Any],
        voice_id: str,
    ) -> Dict[str, Any]:
        segments = polished_script.get("segments", [])
        voice_params = self.build_global_voice_params(voice_id=voice_id)
        timeline_segments: List[Dict[str, Any]] = []
        current_time = 0.0
        sample_rate = 44100

        for seg in segments:
            text = seg.get("content", "")
            # Apply digit slowdown if needed
            ssml = None
            if self._slowdown.is_digit_dense(text):
                ssml = self._slowdown.wrap_ssml(text)

            # Estimate duration: ~3 chars/sec for Chinese
            wc = seg.get("word_count", len(text))
            duration = max(1.0, wc / 3.0)

            # Build segment overrides
            overrides = self.build_segment_overrides(
                segment=seg, digit_slowdown=bool(ssml), global_voice_params=voice_params
            )

            seg_entry = {
                "segment_id": seg["segment_id"],
                "start_sec": round(current_time, 2),
                "end_sec": round(current_time + duration, 2),
                "audio_path": f"phase_4/{seg['segment_id']}.mp3",
                "voice_params": {**voice_params, "overrides": overrides},
                "word_count": wc,
            }
            if ssml:
                seg_entry["ssml_tags"] = ssml

            timeline_segments.append(seg_entry)
            current_time += duration

        return {
            "segments": timeline_segments,
            "total_duration_sec": round(current_time, 2),
            "sample_rate": sample_rate,
        }
