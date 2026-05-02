"""Tests for [SPEC-C-009] Producer Agent Template, Streaming & Decision Rationale.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-5.1 / SPEC-5.7 / SPEC-5.9.
Task card: tasks/SPEC-C/C-009-producer-agent.md.

Acceptance mapping
------------------
AC-1  Prompt template contains exactly 7 mandatory field placeholders.
      -> :class:`TestAC1TemplateHasSevenFields`
AC-2  Rendering with any missing mandatory field raises an exception.
      -> :class:`TestAC2MissingFieldRaises`
AC-3  TTFT (first token arrival) < 3 seconds.
      -> :class:`TestAC3TtftUnder3s`
AC-4  Concatenating all streamed tokens after ``done`` equals the final artifact.
      -> :class:`TestAC4StreamedTokensEqualFinal`
AC-5  ``decision_rationale`` is required in output schema, length >= 20 chars.
      -> :class:`TestAC5DecisionRationaleRequired`
AC-6  Missing ``decision_rationale`` triggers Instructor retry.
      -> :class:`TestAC6MissingRationaleRetries`
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Iterator

import pytest
from pydantic import ValidationError

from src.backend.agents import producer_agent
from src.backend.agents import prompt_templates


REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATE_PATH = REPO_ROOT / "src" / "backend" / "agents" / "prompt_templates.py"

EXPECTED_FIELDS = (
    "role_name",
    "task_description",
    "input_artifacts",
    "output_schema",
    "user_preferences",
    "quality_criteria",
    "prohibitions",
)


def _valid_fields() -> dict[str, str]:
    return {
        "role_name": "ScriptProducer",
        "task_description": "write a 2-minute explainer",
        "input_artifacts": "topic_brief.json",
        "output_schema": "ScriptArtifact",
        "user_preferences": "tone=casual",
        "quality_criteria": "no claims without citation",
        "prohibitions": "no profanity",
    }


# ----------------------------------------------------------------------
# AC-1: template has exactly the 7 mandatory fields
# ----------------------------------------------------------------------


class TestAC1TemplateHasSevenFields:
    """SPEC-5.1 AC-1: exactly 7 placeholders, no more, no less."""

    def test_constant_is_seven_fields(self):
        fields = prompt_templates.PRODUCER_MANDATORY_FIELDS
        assert len(fields) == 7, fields
        assert tuple(fields) == EXPECTED_FIELDS

    def test_template_contains_each_placeholder(self):
        template = prompt_templates.PRODUCER_TEMPLATE
        for field in EXPECTED_FIELDS:
            assert "{" + field + "}" in template, (
                f"template missing placeholder {{{field}}}"
            )

    def test_template_has_no_extra_placeholders(self):
        """A placeholder outside the 7-field set would break rendering.

        Scan the template for any ``{name}`` token and assert the set of
        names equals the mandatory set -- catches both typos and future
        drift.
        """
        template = prompt_templates.PRODUCER_TEMPLATE
        found = set(re.findall(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}", template))
        assert found == set(EXPECTED_FIELDS), (
            f"template placeholder mismatch: {found} vs {set(EXPECTED_FIELDS)}"
        )


# ----------------------------------------------------------------------
# AC-2: missing field raises
# ----------------------------------------------------------------------


class TestAC2MissingFieldRaises:
    """SPEC-5.1 AC-2: a render call missing any of the 7 fields raises."""

    def test_all_fields_present_returns_string(self):
        out = prompt_templates.render_producer_prompt(**_valid_fields())
        assert isinstance(out, str) and out
        for value in _valid_fields().values():
            assert value in out

    @pytest.mark.parametrize("missing", list(EXPECTED_FIELDS))
    def test_each_missing_field_raises(self, missing):
        fields = _valid_fields()
        del fields[missing]
        with pytest.raises(prompt_templates.MissingTemplateFieldError) as excinfo:
            prompt_templates.render_producer_prompt(**fields)
        # error message must name the missing field so callers can log it.
        assert missing in str(excinfo.value)

    def test_empty_string_counts_as_missing(self):
        """An empty value for a mandatory field is as bad as absent -- the
        SPEC-5.1 invariant is that the rendered prompt carries real content
        for every slot, not just a structural stub.
        """
        fields = _valid_fields()
        fields["prohibitions"] = ""
        with pytest.raises(prompt_templates.MissingTemplateFieldError):
            prompt_templates.render_producer_prompt(**fields)


# ----------------------------------------------------------------------
# AC-3: TTFT < 3s
# ----------------------------------------------------------------------


def _stream_chunks(parts: list[str]) -> Iterator[dict[str, Any]]:
    """Yield LiteLLM-shaped streaming chunks for ``parts`` + a terminator."""
    for part in parts:
        yield {
            "choices": [{"index": 0, "delta": {"content": part}, "finish_reason": None}]
        }
    yield {"choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]}


class TestAC3TtftUnder3s:
    """SPEC-5.7 AC: time-to-first-token must be < 3 seconds."""

    def test_first_token_arrives_under_three_seconds(self):
        parts = ["tok1 ", "tok2 ", "tok3"]

        def fake_completion(**_kwargs):
            return _stream_chunks(parts)

        start = time.monotonic()
        first_event_time: float | None = None
        stream = producer_agent.ProducerAgent().stream_generate(
            prompt_fields=_valid_fields(),
            _completion_fn=fake_completion,
        )
        for event in stream:
            if event["type"] == "token":
                first_event_time = time.monotonic() - start
                break
        assert first_event_time is not None, "stream emitted no token event"
        assert first_event_time < 3.0, (
            f"TTFT={first_event_time:.3f}s exceeds SPEC-5.7 3s budget"
        )


# ----------------------------------------------------------------------
# AC-4: streamed tokens concatenated equal the final artifact
# ----------------------------------------------------------------------


class TestAC4StreamedTokensEqualFinal:
    """SPEC-5.7 AC: tokens streamed + final done payload must be consistent."""

    def test_concatenated_tokens_equal_done_payload(self):
        parts = ["Hello", " ", "streaming", " ", "world", "!"]

        def fake_completion(**_kwargs):
            return _stream_chunks(parts)

        events = list(
            producer_agent.ProducerAgent().stream_generate(
                prompt_fields=_valid_fields(),
                _completion_fn=fake_completion,
            )
        )

        tokens = [e["content"] for e in events if e["type"] == "token"]
        done_events = [e for e in events if e["type"] == "done"]

        assert tokens == parts, tokens
        assert len(done_events) == 1, events
        assert done_events[-1]["content"] == "".join(parts)
        # done must be the last event so consumers can stop iterating.
        assert events[-1]["type"] == "done"


# ----------------------------------------------------------------------
# AC-5: decision_rationale required, min_length 20
# ----------------------------------------------------------------------


class TestAC5DecisionRationaleRequired:
    """SPEC-5.9 AC: every Producer output schema carries ``decision_rationale``."""

    def test_field_is_required_in_base_schema(self):
        fields = producer_agent.ProducerOutput.model_fields
        assert "decision_rationale" in fields, fields
        assert fields["decision_rationale"].is_required(), (
            "decision_rationale must be required (no default)"
        )

    def test_short_rationale_raises_validation_error(self):
        with pytest.raises(ValidationError):
            producer_agent.ProducerOutput(decision_rationale="too short")

    def test_exactly_twenty_chars_ok(self):
        out = producer_agent.ProducerOutput(
            decision_rationale="a" * 20,
        )
        assert len(out.decision_rationale) == 20

    def test_subclass_inherits_requirement(self):
        """A subclass used for phase-specific artifacts still inherits the
        required ``decision_rationale`` field -- SPEC-5.9 says "EVERY
        Producer output schema".
        """

        class ScriptArtifact(producer_agent.ProducerOutput):
            body: str

        with pytest.raises(ValidationError):
            ScriptArtifact(body="hi", decision_rationale="x" * 5)

        ok = ScriptArtifact(body="hi", decision_rationale="b" * 25)
        assert ok.body == "hi"


# ----------------------------------------------------------------------
# AC-6: missing / too-short decision_rationale triggers Instructor retry
# ----------------------------------------------------------------------


def _completion_envelope(content: str) -> dict[str, Any]:
    """Minimal OpenAI-chat shape that llm_service understands (non-stream)."""
    return {
        "choices": [{"index": 0, "message": {"role": "assistant", "content": content}}]
    }


class TestAC6MissingRationaleRetries:
    """SPEC-5.9 AC: Instructor retry loop fires on missing/short rationale."""

    def test_retries_until_valid_rationale(self):
        """First attempt omits rationale, second returns a too-short one,
        third returns a valid one -> retry loop from llm_service must
        eventually return the valid model instance.
        """
        responses = iter(
            [
                json.dumps({"body": "draft-1"}),  # missing decision_rationale
                json.dumps(
                    {"body": "draft-2", "decision_rationale": "too short"}
                ),  # below 20 chars
                json.dumps(
                    {
                        "body": "draft-3",
                        "decision_rationale": "detailed rationale over twenty chars",
                    }
                ),  # valid
            ]
        )
        calls: list[dict[str, Any]] = []

        def fake_completion(**kwargs):
            calls.append(kwargs)
            return _completion_envelope(next(responses))

        class ScriptArtifact(producer_agent.ProducerOutput):
            body: str

        out = producer_agent.ProducerAgent().generate(
            prompt_fields=_valid_fields(),
            response_model=ScriptArtifact,
            _completion_fn=fake_completion,
        )

        assert isinstance(out, ScriptArtifact)
        assert out.body == "draft-3"
        assert len(out.decision_rationale) >= 20
        assert len(calls) == 3, (
            "Producer must delegate to the 3-attempt Instructor retry loop"
        )

    def test_all_attempts_missing_rationale_raises(self):
        """If all 3 attempts omit ``decision_rationale``, producer surfaces
        the underlying ``LLMFormatError`` -- no silent fallback.
        """

        def fake_completion(**_kwargs):
            return _completion_envelope(json.dumps({"body": "x"}))

        class ScriptArtifact(producer_agent.ProducerOutput):
            body: str

        from src.backend.services import llm_service

        with pytest.raises(llm_service.LLMFormatError):
            producer_agent.ProducerAgent().generate(
                prompt_fields=_valid_fields(),
                response_model=ScriptArtifact,
                _completion_fn=fake_completion,
            )
