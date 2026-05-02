"""[SPEC-D-008] P10 SubtitleGenerator -- Whisper forced alignment.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.10.3

Strategy:
1. Attempt whisper Python library for word-level timestamps (if installed).
2. Fallback: smart heuristic with phrase grouping, char-weighted timing,
   and inter-segment gaps (0.05s between segments).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class SubtitleGenerator:
    """Generate timed subtitles from audio + text (Whisper forced alignment)."""

    # --- whisper path ---

    @staticmethod
    def _try_whisper_alignment(audio_path: str, text: str) -> Dict[str, Any] | None:
        """Use the openai-whisper Python library for word-level timestamps.

        Returns None if whisper is not installed or if alignment fails.
        """
        try:
            import whisper  # type: ignore[import-untyped]
        except ImportError:
            return None

        try:
            model = whisper.load_model("base")
            result = model.transcribe(audio_path, word_timestamps=True)
        except Exception:
            logger.warning("Whisper transcription failed, falling back to heuristic", exc_info=True)
            return None

        segments = result.get("segments", [])
        if not segments:
            return None

        subtitles: List[Dict[str, Any]] = []
        for seg in segments:
            seg_words = seg.get("words", [])
            if not seg_words:
                subtitles.append({
                    "start_sec": round(seg["start"], 2),
                    "end_sec": round(seg["end"], 2),
                    "text": seg.get("text", "").strip(),
                })
                continue
            for w_info in seg_words:
                subtitles.append({
                    "start_sec": round(w_info["start"], 2),
                    "end_sec": round(w_info["end"], 2),
                    "text": w_info.get("word", "").strip(),
                })

        duration = result.get("duration", max(1.0, len(text) / 3.0))
        return {"subtitles": subtitles, "duration_seconds": duration}

    # --- heuristic fallback ---

    @staticmethod
    def _heuristic_alignment(text: str) -> Dict[str, Any]:
        """Smart heuristic: phrase grouping + char-weighted timing.

        - Group words into phrases of up to 15 chars per subtitle segment.
        - Weight timing by character count (longer words get more time).
        - Add 0.05s inter-segment gaps.
        """
        words = text.split()
        if not words:
            return {"subtitles": [], "duration_seconds": 1.0}

        char_count = sum(len(w) for w in words)
        # Base speaking rate: ~4 chars/s for Chinese-like text
        duration = max(1.0, char_count / 4.0)

        # Phrase grouping: accumulate words until ~15 chars
        phrases: List[List[str]] = []
        current_phrase: List[str] = []
        current_char_len = 0

        for w in words:
            w_len = len(w)
            if current_char_len + w_len > 15 and current_phrase:
                phrases.append(current_phrase)
                current_phrase = [w]
                current_char_len = w_len
            else:
                current_phrase.append(w)
                current_char_len += w_len

        if current_phrase:
            phrases.append(current_phrase)

        # Char-weighted timing proportional to word lengths within phrase
        total_weight = char_count
        gap = 0.05
        total_gap_time = gap * max(len(phrases) - 1, 0)
        available_time = max(0.0, duration - total_gap_time)

        subtitles: List[Dict[str, Any]] = []
        current = 0.0

        for phrase_idx, phrase_words in enumerate(phrases):
            phrase_char_len = sum(len(w) for w in phrase_words)
            phrase_dur = (phrase_char_len / total_weight) * available_time if total_weight > 0 else available_time / max(len(phrases), 1)
            phrase_text = "".join(phrase_words) if all(len(w) <= 2 for w in phrase_words) else " ".join(phrase_words)

            subtitles.append({
                "start_sec": round(current, 2),
                "end_sec": round(current + phrase_dur, 2),
                "text": phrase_text,
            })
            current += phrase_dur + gap

        return {"subtitles": subtitles, "duration_seconds": round(duration, 2)}

    # --- public interface ---

    @staticmethod
    def generate(*, audio_path: str, text: str) -> Dict[str, Any]:
        # Try whisper first, fall back to heuristic.
        whisper_result = SubtitleGenerator._try_whisper_alignment(audio_path, text)
        if whisper_result is not None:
            return whisper_result
        return SubtitleGenerator._heuristic_alignment(text)
