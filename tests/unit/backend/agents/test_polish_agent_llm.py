"""[SPEC-D-004] PolishAgent LLM integration tests.

RED-GREEN-REFACTOR cycle:
  RED: Verify chat_completion called with correct role, output has polished
       content (different from original), voice_direction populated with
       non-default values, key_emphasis non-empty.
  GREEN: Implement LLM call in polish().
  REFACTOR: Clean up under 400 line limit.
"""

from __future__ import annotations

import sys
from unittest.mock import patch

from src.backend.agents.schemas import (
    PolishLLMOutput,
    PolishedSegment,
    VoiceDirection,
)

_MODULE_KEY = "src.backend.agents.polish_agent"


# -- helpers --------------------------------------------------------------


def _clear_agent_cache():
    """Remove the agent module from sys.modules so a fresh import picks up mocks."""
    sys.modules.pop(_MODULE_KEY, None)


def _mock_polished_segments() -> list[PolishedSegment]:
    """Return polished segments with significantly different content from input."""
    return [
        PolishedSegment(
            segment_id="seg_001",
            section_title="AI Breakthroughs Reshape Finance",
            outline_section_ref="sec_001",
            content=(
                "欢迎收看今天的财经深度分析。2025年，人工智能正在"
                "以我们从未想象过的方式重塑金融行业。从华尔街的交易"
                "大厅到普通投资者的手机应用，AI的影响力已经无处不在"
                "——而这仅仅是个开始。"
            ),
            word_count=85,
            key_data_points=[
                {
                    "data_point_id": "dp_001",
                    "value": "AI-driven trading accounts for 70% of US equity volume",
                    "source": "llm_generated",
                    "trust_level": "llm_generated",
                },
            ],
            emotion_tone="excited",
            transition_note="",
            voice_direction=VoiceDirection(
                emotion="excited",
                pace="fast",
                energy="high",
                key_emphasis=["AI", "重塑金融", "无处不在"],
                pause_after=0.8,
                notes="Build energy from opening, punch the key terms",
            ),
        ),
        PolishedSegment(
            segment_id="seg_002",
            section_title="The Evolution of Algorithmic Finance",
            outline_section_ref="sec_002",
            content=(
                "要理解这场变革，我们需要回顾算法金融的演进历程。"
                "从最初简单的规则引擎，到如今能够自我学习的深度神经"
                "网络，这条路走了整整三十年——而真正的加速才刚刚开始。"
            ),
            word_count=70,
            key_data_points=[
                {
                    "data_point_id": "dp_002",
                    "value": "Banks increased AI R&D by 35% YoY (McKinsey 2024)",
                    "source": "llm_generated",
                    "trust_level": "llm_generated",
                },
            ],
            emotion_tone="neutral",
            transition_note="transition from seg_001",
            voice_direction=VoiceDirection(
                emotion="neutral",
                pace="medium",
                energy="medium",
                key_emphasis=["三十年", "加速"],
                pause_after=0.5,
                notes="Steady pacing, let facts land",
            ),
        ),
        PolishedSegment(
            segment_id="seg_003",
            section_title="What This Means for Investors",
            outline_section_ref="sec_003",
            content=(
                "那么作为投资者，这意味着什么？不管你是机构投资者"
                "还是个人散户，理解AI在现代金融市场中的角色已经不是"
                "一个可选项，而是一个必修课。"
            ),
            word_count=62,
            key_data_points=[
                {
                    "data_point_id": "dp_003",
                    "value": "Retail AI-investing platforms grew 200% user base",
                    "source": "llm_generated",
                    "trust_level": "llm_generated",
                },
            ],
            emotion_tone="calm",
            transition_note="transition from seg_002",
            voice_direction=VoiceDirection(
                emotion="calm",
                pace="slow",
                energy="low",
                key_emphasis=["必修课", "不是一个可选项"],
                pause_after=1.0,
                notes="Reflective closing, let the message sink in",
            ),
        ),
    ]


def _mock_llm_output() -> PolishLLMOutput:
    """Return a known LLM output with polished segments."""
    return PolishLLMOutput(
        segments=_mock_polished_segments(),
        is_authoritative_text_source=True,
    )


def _input_segments() -> list[dict]:
    """Original (unpolished) segments as input to PolishAgent."""
    return [
        {
            "segment_id": "seg_001",
            "section_title": "AI Breakthroughs Reshape Finance",
            "outline_section_ref": "sec_001",
            "content": "欢迎收看今天的财经深度分析。AI正在重塑金融行业。",
            "word_count": 24,
            "key_data_points": [
                {
                    "data_point_id": "dp_001",
                    "value": "AI trading 70% of US volume",
                    "source": "llm_generated",
                    "trust_level": "llm_generated",
                },
            ],
            "emotion_tone": "excited",
            "transition_note": "",
        },
        {
            "segment_id": "seg_002",
            "section_title": "The Evolution of Algorithmic Finance",
            "outline_section_ref": "sec_002",
            "content": "算法金融的发展历程。",
            "word_count": 10,
            "key_data_points": [],
            "emotion_tone": "neutral",
            "transition_note": "transition from seg_001",
        },
        {
            "segment_id": "seg_003",
            "section_title": "What This Means for Investors",
            "outline_section_ref": "sec_003",
            "content": "投资者需要了解AI。",
            "word_count": 9,
            "key_data_points": [],
            "emotion_tone": "calm",
            "transition_note": "transition from seg_002",
        },
    ]


def _import_and_polish(segments=None, **overrides):
    """Fresh-import PolishAgent and call polish()."""
    segs = segments if segments is not None else _input_segments()
    from src.backend.agents.polish_agent import PolishAgent

    return PolishAgent.polish(segs, **overrides)


# -- AC: LLM call with correct role --------------------------------------


class TestPolishAgentLLMRole:
    """Verify PolishAgent calls chat_completion with role='polish_agent'."""

    def test_chat_completion_called_with_correct_role(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            _import_and_polish()

            mock_cc.assert_called_once()
            call_kwargs = mock_cc.call_args.kwargs
            assert call_kwargs["role"] == "polish_agent", (
                f"Expected role='polish_agent', got {call_kwargs['role']!r}"
            )

    def test_chat_completion_passes_response_model(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            _import_and_polish()

            call_kwargs = mock_cc.call_args.kwargs
            assert call_kwargs.get("response_model") is PolishLLMOutput, (
                "Expected response_model=PolishLLMOutput"
            )

    def test_chat_completion_messages_contain_segments(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            segments = _input_segments()
            _import_and_polish(segments)

            call_kwargs = mock_cc.call_args.kwargs
            messages = call_kwargs["messages"]
            msg_text = str(messages)
            for seg in segments:
                assert seg["segment_id"] in msg_text, (
                    f"Messages should contain {seg['segment_id']}"
                )


# -- AC: Output structure -------------------------------------------------


class TestPolishAgentOutputStructure:
    """Verify output has polished content, voice_direction, key_emphasis."""

    def test_output_contains_is_authoritative_flag(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_polish()

            assert result.get("is_authoritative_text_source") is True, (
                "Output must have is_authoritative_text_source=true"
            )

    def test_polished_content_differs_from_original(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            original = _input_segments()
            result = _import_and_polish(original)

            for orig_seg, polished_seg in zip(original, result["segments"]):
                assert polished_seg["content"] != orig_seg["content"], (
                    f"Segment {orig_seg['segment_id']} content unchanged "
                    f"after polishing"
                )

    def test_each_segment_has_voice_direction_with_all_fields(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_polish()

            required_vd_fields = [
                "emotion", "pace", "energy", "key_emphasis",
                "pause_after", "notes",
            ]
            for seg in result["segments"]:
                vd = seg.get("voice_direction")
                assert vd is not None, (
                    f"Segment {seg['segment_id']} missing voice_direction"
                )
                for field in required_vd_fields:
                    assert field in vd, (
                        f"voice_direction missing '{field}' in "
                        f"segment {seg['segment_id']}"
                    )

    def test_key_emphasis_is_non_empty(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_polish()

            for seg in result["segments"]:
                vd = seg["voice_direction"]
                ke = vd.get("key_emphasis", [])
                assert len(ke) > 0, (
                    f"Segment {seg['segment_id']} key_emphasis is empty"
                )
                assert all(isinstance(item, str) for item in ke), (
                    "key_emphasis items must be strings"
                )

    def test_voice_direction_not_all_neutral_medium(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_polish()

            paces = {seg["voice_direction"]["pace"] for seg in result["segments"]}
            energies = {seg["voice_direction"]["energy"] for seg in result["segments"]}

            # Not all segments should have the same pace/energy
            assert len(paces) > 1, (
                f"All segments have same pace '{paces}', expected variety"
            )
            assert len(energies) > 1, (
                f"All segments have same energy '{energies}', expected variety"
            )

    def test_polish_handles_empty_input(self):
        _clear_agent_cache()
        mock_out = PolishLLMOutput(segments=[], is_authoritative_text_source=True)

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_polish([])

            assert result["segments"] == []
            assert result["is_authoritative_text_source"] is True
