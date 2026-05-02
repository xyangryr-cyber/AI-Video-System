"""[SPEC-D-003] ScriptAgent LLM integration tests.

RED-GREEN-REFACTOR cycle:
  RED: Verify chat_completion called with correct role, segments have natural
       language content (not "第N部分" template), word_count from actual output.
  GREEN: Implement LLM call in produce().
  REFACTOR: Clean up under 400 line limit.
"""

from __future__ import annotations

import sys
from unittest.mock import patch

from src.backend.agents.schemas import (
    DataPoint,
    ScriptLLMOutput,
    ScriptSegment,
)

_MODULE_KEY = "src.backend.agents.script_agent"


# -- helpers --------------------------------------------------------------


def _clear_agent_cache():
    """Remove the agent module from sys.modules so a fresh import picks up mocks."""
    sys.modules.pop(_MODULE_KEY, None)


def _mock_segments() -> list[ScriptSegment]:
    """Return 5 script segments with natural language content."""
    return [
        ScriptSegment(
            segment_id="seg_001",
            section_title="AI Breakthroughs Reshape Finance",
            outline_section_ref="sec_001",
            content=(
                "欢迎收看今天的财经深度分析。2025年，人工智能正在以我们从未"
                "想象过的方式重塑金融行业。从华尔街的交易大厅到普通投资者的"
                "手机应用，AI的影响力已经无处不在。"
            ),
            word_count=72,
            key_data_points=[
                DataPoint(
                    data_point_id="dp_001",
                    value="AI-driven trading accounts for 70% of US equity volume",
                    source="llm_generated",
                    trust_level="llm_generated",
                ),
            ],
            emotion_tone="excited",
            transition_note="",
        ),
        ScriptSegment(
            segment_id="seg_002",
            section_title="The Evolution of Algorithmic Finance",
            outline_section_ref="sec_002",
            content=(
                "要理解这场变革，我们需要回顾算法金融的演进历程。从最初"
                "简单的规则引擎，到如今能够自我学习的深度神经网络，这条路"
                "走了三十年。"
            ),
            word_count=56,
            key_data_points=[
                DataPoint(
                    data_point_id="dp_002",
                    value="Major banks increased AI R&D by 35% YoY (McKinsey 2024)",
                    source="llm_generated",
                    trust_level="llm_generated",
                ),
            ],
            emotion_tone="neutral",
            transition_note="transition from seg_001",
        ),
        ScriptSegment(
            segment_id="seg_003",
            section_title="Why Traditional Risk Models Are Failing",
            outline_section_ref="sec_003",
            content=(
                "传统的风险管理模型正在失效。基于历史数据的VaR模型无法"
                "捕捉黑天鹅事件，而AI驱动的实时风险监测系统能够在市场异常"
                "出现前48小时发出预警信号。"
            ),
            word_count=66,
            key_data_points=[
                DataPoint(
                    data_point_id="dp_003",
                    value="AI models detected anomalies 48 hours before market moves",
                    source="llm_generated",
                    trust_level="llm_generated",
                ),
            ],
            emotion_tone="neutral",
            transition_note="transition from seg_002",
        ),
        ScriptSegment(
            segment_id="seg_004",
            section_title="The Tipping Point: AI-Native Hedge Funds",
            outline_section_ref="sec_004",
            content=(
                "真正的转折点出现在AI原生对冲基金上。2024年，这些完全由"
                "AI驱动的基金平均回报率达到28%，而传统对冲基金仅为12%。"
                "这个差距不是偶然，而是范式转换的信号。"
            ),
            word_count=75,
            key_data_points=[
                DataPoint(
                    data_point_id="dp_004",
                    value="AI-native hedge funds returned 28% vs 12% traditional",
                    source="llm_generated",
                    trust_level="llm_generated",
                ),
            ],
            emotion_tone="excited",
            transition_note="transition from seg_003",
        ),
        ScriptSegment(
            segment_id="seg_005",
            section_title="What This Means for Investors in 2025",
            outline_section_ref="sec_005",
            content=(
                "那么作为投资者，这意味着什么？不管你是机构投资者还是个人"
                "散户，理解AI在现代金融市场中的角色已经不是一个可选项，"
                "而是一个必修课。"
            ),
            word_count=64,
            key_data_points=[
                DataPoint(
                    data_point_id="dp_005",
                    value="Retail AI-investing platforms grew 200% user base in 2024",
                    source="llm_generated",
                    trust_level="llm_generated",
                ),
            ],
            emotion_tone="calm",
            transition_note="transition from seg_004",
        ),
    ]


def _mock_llm_output() -> ScriptLLMOutput:
    """Return a known LLM output with natural language script segments."""
    return ScriptLLMOutput(segments=_mock_segments())


def _valid_produce_kwargs():
    """Return valid kwargs for ScriptAgent.produce()."""
    return {
        "requirements": {
            "project_id": "proj_001",
            "title": "AI in Finance 2025",
            "target_word_count": {"min": 800, "max": 1200},
        },
        "outline": {
            "sections": [
                {"section_id": "sec_001", "title": "Hook Section"},
                {"section_id": "sec_002", "title": "Context Section"},
                {"section_id": "sec_003", "title": "Argument Section"},
                {"section_id": "sec_004", "title": "Climax Section"},
                {"section_id": "sec_005", "title": "Conclusion Section"},
            ],
        },
    }


def _import_and_produce(**overrides):
    """Fresh-import ScriptAgent and call produce()."""
    kwargs = _valid_produce_kwargs()
    kwargs.update(overrides)
    from src.backend.agents.script_agent import ScriptAgent

    return ScriptAgent.produce(**kwargs)


# -- AC: LLM call with correct role --------------------------------------


class TestScriptAgentLLMRole:
    """Verify ScriptAgent calls chat_completion with role='script_agent'."""

    def test_chat_completion_called_with_correct_role(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            _import_and_produce()

            mock_cc.assert_called_once()
            call_kwargs = mock_cc.call_args.kwargs
            assert call_kwargs["role"] == "script_agent", (
                f"Expected role='script_agent', got {call_kwargs['role']!r}"
            )

    def test_chat_completion_passes_response_model(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            _import_and_produce()

            call_kwargs = mock_cc.call_args.kwargs
            assert call_kwargs.get("response_model") is ScriptLLMOutput, (
                "Expected response_model=ScriptLLMOutput"
            )

    def test_chat_completion_messages_contain_requirements_and_outline(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            kwargs = _valid_produce_kwargs()
            _import_and_produce()

            call_kwargs = mock_cc.call_args.kwargs
            messages = call_kwargs["messages"]
            msg_text = str(messages)
            assert "target_word_count" in msg_text, (
                "Messages should contain requirements"
            )
            assert "sec_001" in msg_text, "Messages should contain outline sections"


# -- AC: Output structure -------------------------------------------------


class TestScriptAgentOutputStructure:
    """Verify segments have natural language content, real word_counts."""

    def test_output_is_list_of_segments(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_produce()

            assert isinstance(result, list), "Output should be a list of segments"
            assert len(result) == 5, f"Expected 5 segments, got {len(result)}"

    def test_segment_content_is_natural_language_not_template(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_produce()

            for seg in result:
                content = seg["content"]
                # Should NOT start with "第N部分" (template placeholder)
                assert not content.startswith("第"), (
                    f"Template-style content found: {content[:50]}..."
                )

    def test_segment_word_count_from_actual_content_length(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_produce()

            for seg in result:
                content = seg["content"]
                wc = seg["word_count"]
                # Word count should roughly match content length (Chinese chars)
                actual_chars = len(content.replace(" ", "").replace("\n", ""))
                assert wc > 0, f"word_count should be positive, got {wc}"
                # Allow reasonable deviation (LLM might count differently)
                assert abs(wc - actual_chars) <= actual_chars, (
                    f"word_count {wc} too far from actual chars {actual_chars}"
                )

    def test_segments_have_data_points_with_llm_generated_trust(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_produce()

            for seg in result:
                dps = seg.get("key_data_points", [])
                assert len(dps) > 0, f"Segment {seg['segment_id']} has no data points"
                for dp in dps:
                    assert dp["trust_level"] == "llm_generated", (
                        f"Data point trust_level should be llm_generated, "
                        f"got {dp['trust_level']!r}"
                    )
                    assert "data_point_id" in dp
                    assert "value" in dp
                    assert dp["value"], "data_point value should not be empty"

    def test_emotion_tone_variety(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_produce()

            emotions = {seg["emotion_tone"] for seg in result}
            # Mock has excited, neutral, calm
            assert "excited" in emotions, f"Expected 'excited' in emotions: {emotions}"
            assert "calm" in emotions, f"Expected 'calm' in emotions: {emotions}"

    def test_handles_empty_outline_sections(self):
        _clear_agent_cache()
        mock_out = ScriptLLMOutput(segments=[])

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_produce(outline={"sections": []})

            assert isinstance(result, list)
            assert len(result) == 0
