"""[SPEC-D-002] RequirementsAgent LLM integration tests.

RED-GREEN-REFACTOR cycle:
  RED: Verify chat_completion called with correct role, verify output structure.
  GREEN: Implement LLM call in produce().
  REFACTOR: Clean up under 400 line limit.
"""

from __future__ import annotations

import sys
from unittest.mock import patch

import pytest

from src.backend.agents.schemas import (
    RequirementsLLMOutput,
    SubtitlePreferences,
    VoicePreferences,
)

_MODULE_KEY = "src.backend.agents.requirements_agent"


# -- helpers --------------------------------------------------------------


def _clear_agent_cache():
    """Remove the agent module from sys.modules so a fresh import picks up mocks."""
    sys.modules.pop(_MODULE_KEY, None)


def _mock_llm_output() -> RequirementsLLMOutput:
    """Return a known LLM output for test assertions."""
    return RequirementsLLMOutput(
        clarified_topic=(
            "An in-depth analysis of AI's impact on the financial sector, "
            "covering key trends in 2025 including automated trading, "
            "risk management AI, and regulatory technology."
        ),
        voice_preferences=VoicePreferences(
            gender="female",
            tone="professional",
            speed="medium",
        ),
        subtitle_preferences=SubtitlePreferences(
            position="bottom",
            font_size="medium",
        ),
    )


def _valid_produce_kwargs():
    """Return valid kwargs for RequirementsAgent.produce()."""
    return {
        "project_id": "proj_001",
        "title": "AI in Finance 2025",
        "topic": "How AI is transforming the financial industry",
        "duration_class": "medium",
        "platform": "web",
        "category_level1": "finance",
        "category_level2": "technology",
        "narrative_template": "chronological",
        "target_duration_seconds": 600,
        "target_word_count_min": 1600,
        "target_word_count_max": 2000,
    }


def _import_and_produce(**overrides):
    """Fresh-import RequirementsAgent and call produce()."""
    kwargs = _valid_produce_kwargs()
    kwargs.update(overrides)
    from src.backend.agents.requirements_agent import RequirementsAgent

    return RequirementsAgent().produce(**kwargs)


# -- AC: LLM call with correct role --------------------------------------


class TestRequirementsAgentLLMRole:
    """Verify RequirementsAgent calls chat_completion with role='requirements_agent'."""

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
            assert call_kwargs["role"] == "requirements_agent", (
                f"Expected role='requirements_agent', got {call_kwargs['role']!r}"
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
            assert call_kwargs.get("response_model") is RequirementsLLMOutput, (
                "Expected response_model=RequirementsLLMOutput"
            )

    def test_chat_completion_messages_contain_title_and_topic(self):
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
            user_content = str(messages)
            assert kwargs["title"] in user_content, "Messages should contain title"
            assert kwargs["topic"] in user_content, "Messages should contain topic"


# -- AC: Output structure -------------------------------------------------


class TestRequirementsAgentOutputStructure:
    """Verify the returned dict contains LLM-populated fields."""

    def test_output_contains_clarified_topic_from_llm(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_produce()

            assert "clarified_topic" in result, "Output missing clarified_topic"
            assert result["clarified_topic"] == mock_out.clarified_topic

    def test_output_contains_voice_preferences_from_llm(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_produce()

            vp = result["voice_preferences"]
            assert vp["gender"] == "female"
            assert vp["tone"] == "professional"
            assert vp["speed"] == "medium"

    def test_output_contains_subtitle_preferences_from_llm(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            result = _import_and_produce()

            sp = result["subtitle_preferences"]
            assert sp["position"] == "bottom"
            assert sp["font_size"] == "medium"

    def test_output_retains_original_fields(self):
        _clear_agent_cache()
        mock_out = _mock_llm_output()

        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=mock_out,
        ) as mock_cc:
            kwargs = _valid_produce_kwargs()
            result = _import_and_produce()

            assert result["project_id"] == kwargs["project_id"]
            assert result["title"] == kwargs["title"]
            assert result["duration_class"] == kwargs["duration_class"]
            assert result["platform"] == kwargs["platform"]
            assert result["target_duration_seconds"] == kwargs["target_duration_seconds"]


# -- AC: Parameter validation preserved ----------------------------------


class TestRequirementsAgentValidation:
    """Verify original parameter validation (word_count/duration) is preserved."""

    def test_word_count_duration_consistency_fails_when_deviation_over_10_percent(self):
        _clear_agent_cache()
        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=_mock_llm_output(),
        ):
            from src.backend.agents.requirements_agent import RequirementsAgent

            agent = RequirementsAgent()
            kwargs = _valid_produce_kwargs()
            # Far too few words for 600 seconds (should be ~1800 chars)
            kwargs["target_word_count_min"] = 100
            kwargs["target_word_count_max"] = 200

            with pytest.raises(ValueError, match="word_count"):
                agent.produce(**kwargs)

    def test_word_count_duration_consistency_passes_when_within_10_percent(self):
        _clear_agent_cache()
        with patch(
            "src.backend.services.llm_service.chat_completion",
            return_value=_mock_llm_output(),
        ) as mock_cc:
            result = _import_and_produce()
            assert "clarified_topic" in result
