"""[SPEC-C-009] Producer Agent -- template + streaming + decision_rationale.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-5.1 / SPEC-5.7 / SPEC-5.9.

What this module is
-------------------
The Producer Agent is the class that turns a **prompt template fill-in**
into a **streamed artifact** carrying an auditable ``decision_rationale``.
Three orthogonal concerns live here:

1. **Template fill-in (SPEC-5.1)** -- delegate to
   :mod:`src.backend.agents.prompt_templates`. Missing any of the 7
   mandatory fields raises at render time.
2. **Streaming (SPEC-5.7)** -- :meth:`ProducerAgent.stream_generate` is a
   generator that yields ``{"type": "token", "content": str}`` for each
   streaming delta and a final ``{"type": "done", "content": str}``
   carrying the full artifact. The first yielded event is the TTFT marker.
3. **Decision rationale (SPEC-5.9)** -- :class:`ProducerOutput` declares
   ``decision_rationale: str`` with ``min_length=20``. Subclasses (one per
   phase artifact) inherit the constraint, so any Producer output in the
   system is guaranteed to carry a >=20-char rationale. Missing / short
   values fail Pydantic validation, which drives the Instructor retry loop
   in :func:`src.backend.services.llm_service.chat_completion`.

Stateless by design
-------------------
:class:`ProducerAgent` holds no instance attributes. Every invocation is a
fresh function call through class methods -- so horizontal scaling and
cross-request isolation are structural, not enforced at runtime.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator, Mapping
from typing import Any, TypeVar, cast

from pydantic import BaseModel, Field

from src.backend.agents.prompt_templates import render_producer_prompt
from src.backend.services import llm_service


class ProducerOutput(BaseModel):
    """Base schema for every Producer output artifact (SPEC-5.9).

    Subclass this for each phase artifact (``ScriptArtifact``,
    ``StoryboardArtifact``, ...). The ``decision_rationale`` field is
    required with a 20-char floor, so every phase produces explainable
    output or fails validation -- which triggers llm_service's retry loop.
    """

    decision_rationale: str = Field(
        ...,
        min_length=20,
        description=(
            "Why the Producer chose this output (SPEC-5.9); "
            "min 20 chars enforces substance over a stub."
        ),
    )


M = TypeVar("M", bound=ProducerOutput)


class ProducerAgent:
    """Stateless Producer surface: prompt build, streaming, structured call."""

    # -- Prompt --------------------------------------------------------

    @staticmethod
    def build_prompt(fields: Mapping[str, str]) -> str:
        """Render the SPEC-5.1 template. Raises if any field missing/empty."""
        return render_producer_prompt(**dict(fields))

    # -- Streaming (SPEC-5.7) -----------------------------------------

    @staticmethod
    def stream_generate(
        *,
        prompt_fields: Mapping[str, str],
        _completion_fn: Callable[..., Iterable[Any]] | None = None,
        role: str = "producer",
        config_path: str | None = None,
        **extra: Any,
    ) -> Iterator[dict[str, Any]]:
        """Stream Producer output as ``token`` events plus a final ``done``.

        Parameters
        ----------
        prompt_fields
            The 7 SPEC-5.1 fields. Missing values raise at prompt build.
        _completion_fn
            Dependency-injection hook for tests / alternative transports.
            The callable must return an iterable of OpenAI-streaming-shaped
            chunks (``{"choices":[{"delta":{"content": str}, ...}]}``).
            If ``None``, the call is routed through LiteLLM via
            :func:`llm_service._default_completion` with ``stream=True``.
        role
            Model-config role key (SPEC-5.5). Defaults to ``"producer"``.
        config_path, **extra
            Forwarded to model resolution / the transport.

        Yields
        ------
        dict
            ``{"type": "token", "content": str}`` per non-empty delta, then
            a single ``{"type": "done", "content": str}`` carrying the
            concatenation of all streamed deltas (SPEC-5.7 AC).
        """
        prompt = ProducerAgent.build_prompt(prompt_fields)
        model = llm_service.resolve_model(role, config_path=config_path)
        messages = [{"role": "user", "content": prompt}]

        transport: Callable[..., Iterable[Any]]
        if _completion_fn is not None:
            transport = _completion_fn
        else:
            transport = llm_service._default_completion

        stream = transport(model=model, messages=messages, stream=True, **extra)

        buffer: list[str] = []
        for chunk in stream:
            content = _extract_delta_content(chunk)
            if content:
                buffer.append(content)
                yield {"type": "token", "content": content}
        yield {"type": "done", "content": "".join(buffer)}

    # -- Structured call with retry (SPEC-5.9) ------------------------

    @staticmethod
    def generate(
        *,
        prompt_fields: Mapping[str, str],
        response_model: type[M],
        _completion_fn: Callable[..., Any] | None = None,
        role: str = "producer",
        config_path: str | None = None,
        **extra: Any,
    ) -> M:
        """Structured Producer call: renders prompt, delegates to the
        Instructor-style retry loop in :func:`llm_service.chat_completion`.

        ``response_model`` must subclass :class:`ProducerOutput` so the
        20-char ``decision_rationale`` floor is part of the validation --
        missing / short rationales trigger the retry on the llm_service
        side (SPEC-5.9 AC). On exhaustion, :class:`LLMFormatError` bubbles.
        """
        if not issubclass(response_model, ProducerOutput):
            raise TypeError(
                "response_model must subclass ProducerOutput "
                "(SPEC-5.9 requires decision_rationale on every artifact)"
            )
        prompt = ProducerAgent.build_prompt(prompt_fields)
        messages = [{"role": "user", "content": prompt}]
        result = llm_service.chat_completion(
            role=role,
            messages=messages,
            response_model=response_model,
            config_path=config_path,
            _completion_fn=_completion_fn,
            **extra,
        )
        return cast(M, result)


def _extract_delta_content(chunk: Any) -> str:
    """Pull ``delta.content`` out of a LiteLLM / OpenAI streaming chunk.

    Accepts dict-shaped chunks (tests) and attribute-access objects
    (LiteLLM real return type). Missing / ``None`` content -> empty string.
    """
    try:
        if isinstance(chunk, Mapping):
            choices = chunk.get("choices") or []
            if not choices:
                return ""
            first = choices[0]
            delta = first.get("delta") if isinstance(first, Mapping) else first.delta
            if isinstance(delta, Mapping):
                content = delta.get("content")
            else:
                content = getattr(delta, "content", None)
        else:
            choices = getattr(chunk, "choices", None) or []
            if not choices:
                return ""
            delta = choices[0].delta
            content = getattr(delta, "content", None)
    except (AttributeError, KeyError, IndexError, TypeError):
        return ""
    return str(content) if content else ""


__all__ = [
    "ProducerAgent",
    "ProducerOutput",
]
