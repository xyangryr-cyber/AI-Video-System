"""[SPEC-D-003] P3 PolishAgent -- produces polished_script with voice_direction.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.3
"""

from __future__ import annotations

from typing import Any

from src.backend.agents.schemas import PolishLLMOutput
from src.backend.services.llm_service import chat_completion


class PolishAgent:
    """Polish raw script segments into voice-ready polished_script.

    Stateless -- every call creates fresh output.
    Calls LLM via chat_completion to polish scripts with conversational tone,
    rhythm markers, and emotional direction.
    """

    @staticmethod
    def polish(segments: list[dict[str, Any]]) -> dict[str, Any]:
        if not segments:
            return {
                "segments": [],
                "is_authoritative_text_source": True,
            }

        try:
            llm_result: PolishLLMOutput = chat_completion(
                role="polish_agent",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a financial video script polisher. "
                            "Rewrite raw scripts to be more conversational "
                            "and suitable for voice narration. Add rhythm "
                            "markers and emotional direction. Each segment "
                            "must have voice_direction with specific "
                            "emotion, pace, energy, key_emphasis (list of "
                            "phrases to emphasize), pause_after (seconds), "
                            "and notes. The polished content must be "
                            "significantly different from the original -- "
                            "expand, add transitions, make it flow naturally "
                            "when spoken aloud. key_emphasis must be non-empty "
                            "for every segment. Vary the voice_direction across "
                            "segments -- do not use neutral/medium for all."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Original script segments: {segments}\n\n"
                            "Polish each segment: make it conversational, "
                            "add rhythm markers, provide emotional direction. "
                            "Each segment's voice_direction must include "
                            "emotion, pace, energy, key_emphasis (non-empty "
                            "list of key phrases to emphasize), pause_after "
                            "(float seconds), and notes. Content must be "
                            "substantially rewritten, not just copied."
                        ),
                    },
                ],
                response_model=PolishLLMOutput,
            )
            return {
                "segments": [seg.model_dump() for seg in llm_result.segments],
                "is_authoritative_text_source": llm_result.is_authoritative_text_source,
            }
        except Exception:
            # Fallback: pass through with basic voice direction
            fallback_segments = []
            for i, seg in enumerate(segments):
                fallback_segments.append(
                    {
                        "segment_id": seg.get("segment_id", f"seg_{i:03d}"),
                        "section_title": seg.get("section_title", f"第{i + 1}节"),
                        "outline_section_ref": seg.get("outline_section_ref", f"sec_{i}"),
                        "content": seg.get("content", ""),
                        "word_count": seg.get("word_count", len(seg.get("content", ""))),
                        "key_data_points": seg.get("key_data_points", []),
                        "emotion_tone": seg.get("emotion_tone", "neutral"),
                        "transition_note": seg.get("transition_note", ""),
                        "voice_direction": {
                            "emotion": "calm",
                            "pace": "medium",
                            "energy": "moderate",
                            "key_emphasis": [seg.get("section_title", "")[:20]],
                            "pause_after": 0.3,
                            "notes": "Fallback voice direction",
                        },
                    }
                )
            return {
                "segments": fallback_segments,
                "is_authoritative_text_source": True,
            }
