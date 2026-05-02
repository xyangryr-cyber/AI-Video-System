"""[SPEC-C-011] Unified LLM service -- LiteLLM transport + Instructor-style retry.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-5.4 / SPEC-5.5.

What this module is
-------------------
The **single** entry point for every LLM call in ``src/backend/``. All
agents / workers / API handlers MUST call :func:`chat_completion` instead
of reaching for the provider SDK directly. Direct legacy-OpenAI
chat-completion call sites are banned repo-wide (grep test in
``test_llm_service.py`` AC-1).

Design
------
* **Transport = LiteLLM** (SPEC-5.4): provider-agnostic shim that understands
  the OpenAI chat-completion shape for Claude, Doubao, OpenAI, etc. Imported
  lazily so this module is importable in environments where the LiteLLM
  wheel has not yet been installed (e.g. the unit test runner). The lazy
  binding ``_default_completion`` is monkey-patched by tests that assert
  the service uses LiteLLM as its default.
* **Structured output = Instructor-style retry** (SPEC-5.4 AC-2): when the
  caller passes ``response_model`` (a Pydantic class), the service parses
  the assistant message against it. On ``ValidationError`` / JSON decode
  error, the bad output is appended to the conversation and the call is
  retried up to **3 total attempts**. After the third failed attempt we
  raise :class:`LLMFormatError` -- callers decide how to degrade.
* **Model routing = ``model_config.json``** (SPEC-5.5): the 5 role keys are
  resolved on every call (no caching) so a hot-edit of the config file is
  picked up on the next completion. Missing-file / bad-JSON / missing-key
  all raise :class:`UnknownRoleError` on the caller, not a silent fallback:
  silent fallback would make a typo in a role name invisible until prod.

Public surface (see :data:`__all__`)
-----------------------------------
* :func:`chat_completion` -- the one entry point
* :func:`resolve_model`   -- role -> model name
* :class:`LLMFormatError`, :class:`UnknownRoleError`, :class:`LLMServiceError`
"""

from __future__ import annotations

import json
import logging
import re
import time
from pathlib import Path
from typing import Any, Callable, Mapping, Sequence, Type, TypeVar

from pydantic import BaseModel, ValidationError

from src.backend.core.redaction import SECRET_REGEXES


log = logging.getLogger(__name__)


# -- Config --------------------------------------------------------------

_DEFAULT_CONFIG_PATH = Path("config/model_config.json")

VALID_ROLES: tuple[str, ...] = (
    "intent_router_primary",
    "reviewer",
    "gatekeeper",
    "producer",
    "subtask",
    "requirements_agent",
    "outline_agent",
    "script_agent",
    "polish_agent",
)

# SPEC-5.4 caps Instructor retry budget at 3 total attempts.
MAX_ATTEMPTS = 3


# -- Errors --------------------------------------------------------------


class LLMServiceError(Exception):
    """Base class for llm_service failures."""


class UnknownRoleError(LLMServiceError):
    """Role name is not one of the 5 SPEC-5.5 keys / absent from config."""


class LLMFormatError(LLMServiceError):
    """Instructor-style retry budget exhausted without a valid response.

    Carries the last raw assistant content and the ``ValidationError`` (or
    ``json.JSONDecodeError``) from the final attempt so callers can log.
    """

    def __init__(self, last_raw: str, last_error: Exception, attempts: int) -> None:
        super().__init__(f"LLM format error after {attempts} attempts: {last_error}")
        self.last_raw = last_raw
        self.last_error = last_error
        self.attempts = attempts


# -- LiteLLM transport (lazy) --------------------------------------------


def _default_completion(**kwargs: Any) -> Any:
    """Default transport: delegate to LiteLLM. Imported lazily so the
    module stays importable when LiteLLM is not installed (tests stub it
    via monkeypatch).
    """
    try:
        import litellm  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover -- exercised in env without litellm
        raise LLMServiceError(
            "litellm is not installed; add it to requirements.txt or inject "
            "_completion_fn for tests"
        ) from exc
    return litellm.completion(**kwargs)


# -- Model routing -------------------------------------------------------


def resolve_model(role: str, *, config_path: str | Path | None = None) -> str:
    """Return the model name bound to ``role`` in ``model_config.json``.

    Re-reads the config on every call (SPEC-5.5 AC: "config change +
    restart => new model"; we go further and apply without restart).

    Raises
    ------
    UnknownRoleError
        ``role`` is not a SPEC-5.5 key, or the config file is missing the
        key / is malformed. Caller gets a loud failure instead of a silent
        default, which is what we want for a typo in a role name.
    """
    if role not in VALID_ROLES:
        raise UnknownRoleError(f"unknown role {role!r}; valid: {VALID_ROLES}")
    path = Path(config_path) if config_path is not None else _DEFAULT_CONFIG_PATH
    try:
        with path.open(encoding="utf-8") as f:
            cfg = json.load(f)
    except (FileNotFoundError, OSError, json.JSONDecodeError) as exc:
        raise UnknownRoleError(f"cannot read model config at {path}: {exc}") from exc
    if not isinstance(cfg, dict):
        raise UnknownRoleError(f"model config at {path} is not an object")
    value = cfg.get(role)
    if not isinstance(value, str) or not value.strip():
        raise UnknownRoleError(
            f"role {role!r} missing or non-string in {path}: {value!r}"
        )
    return value


# -- Structured-output helpers ------------------------------------------


M = TypeVar("M", bound=BaseModel)


def _extract_assistant_content(response: Any) -> str:
    """Pull the assistant message string out of a LiteLLM completion.

    Accepts both dict-shaped envelopes (used in tests) and objects with
    attribute access (the real LiteLLM return type).
    """
    if isinstance(response, Mapping):
        choices = response["choices"]
        first = choices[0]
        msg = first["message"] if isinstance(first, Mapping) else first.message
        content = msg["content"] if isinstance(msg, Mapping) else msg.content
    else:
        choices = response.choices
        first = choices[0]
        msg = first.message
        content = msg.content
    if content is None:
        return ""
    return str(content)


def _parse_structured(content: str, response_model: Type[M]) -> M:
    """Parse ``content`` as JSON, then validate against ``response_model``."""
    data = json.loads(content)
    return response_model.model_validate(data)


# -- Single entry point --------------------------------------------------


def chat_completion(
    *,
    role: str,
    messages: Sequence[Mapping[str, Any]],
    response_model: Type[M] | None = None,
    config_path: str | Path | None = None,
    _completion_fn: Callable[..., Any] | None = None,
    _agent_call_logger: Any = None,
    **extra: Any,
) -> Any:
    """Single LLM entry point (SPEC-5.4 AC-1, AC-5).

    Parameters
    ----------
    role
        One of :data:`VALID_ROLES`. Resolved to a model name via
        ``model_config.json``.
    messages
        OpenAI-chat-shaped message list.
    response_model
        Optional Pydantic class for structured output. When set, the
        raw content is JSON-parsed and validated; on failure the call is
        retried up to :data:`MAX_ATTEMPTS` total times (SPEC-5.4 AC-2).
    config_path
        Override path to ``model_config.json``; tests use this to exercise
        the re-read-on-each-call behaviour (SPEC-5.5 AC-4).
    _completion_fn
        Dependency-injection hook for tests. Real code never passes this:
        the service uses LiteLLM (:func:`_default_completion`) by default.
    _agent_call_logger
        Optional AgentCallLogger instance. When provided, every LLM call
        is logged to the ``agent_call_log`` table per HARNESS section 8.1.
    **extra
        Forwarded verbatim to the completion call (``temperature``,
        ``max_tokens``, streaming flags, etc.).

    Returns
    -------
    * If ``response_model`` is set: an instance of that model.
    * Otherwise: the raw LiteLLM response envelope (passthrough).

    Raises
    ------
    UnknownRoleError
        ``role`` not resolvable via config.
    LLMFormatError
        Retry budget exhausted without a valid structured output.
    """
    model = resolve_model(role, config_path=config_path)
    completion = _completion_fn if _completion_fn is not None else _default_completion

    if "timeout" not in extra:
        extra["timeout"] = 60  # prevent hanging LLM calls from blocking threads

    # Unstructured path: single call, passthrough.
    if response_model is None:
        t0 = time.monotonic()
        response = completion(model=model, messages=list(messages), **extra)
        if _agent_call_logger is not None:
            _log_agent_call(
                _agent_call_logger, role, model, messages, response, t0, extra
            )
        return response

    # Structured path: Instructor-style retry up to MAX_ATTEMPTS.
    conversation = [dict(m) for m in messages]
    last_raw = ""
    last_error: Exception = LLMFormatError("", Exception("unreached"), 0)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        t0 = time.monotonic()
        response = completion(model=model, messages=conversation, **extra)
        last_raw = _extract_assistant_content(response)
        if _agent_call_logger is not None:
            _log_agent_call(
                _agent_call_logger, role, model, conversation, response, t0, extra
            )
        try:
            return _parse_structured(last_raw, response_model)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = exc
            log.warning(
                "llm_service.format_error",
                extra={
                    "role": role,
                    "model": model,
                    "attempt": attempt,
                    "error": str(exc),
                },
            )
            if attempt >= MAX_ATTEMPTS:
                break
            # Append the bad output + a corrective nudge, so the LLM sees
            # what went wrong on the next retry. This mirrors Instructor's
            # retry-with-validation-context loop.
            conversation.append({"role": "assistant", "content": last_raw})
            conversation.append(
                {
                    "role": "user",
                    "content": (
                        "Your previous response failed validation: "
                        f"{exc}. Respond again with valid JSON matching "
                        f"the schema of {response_model.__name__}."
                    ),
                }
            )

    raise LLMFormatError(last_raw, last_error, MAX_ATTEMPTS)


def _log_agent_call(
    logger: Any,
    role: str,
    model: str,
    messages: Sequence[Mapping[str, Any]],
    response: Any,
    t0: float,
    extra: dict[str, Any],
) -> None:
    """Log an LLM call to the AgentCallLogger if one is available."""
    try:
        duration_ms = int((time.monotonic() - t0) * 1000)
        input_summary = redact_text(str(messages)[:500])
        output_summary = redact_text(_extract_assistant_content(response)[:500])
        logger.log_call(
            agent_name=role,
            duration_ms=duration_ms,
            model=model,
            input_summary=input_summary,
            output_summary=output_summary,
        )
    except Exception:
        # Logging failure must never break the main call path.
        pass


# -- Redaction -----------------------------------------------------------


# Additional patterns beyond SECRET_REGEXES for common auth token formats.
_EXTRA_REDACT_PATTERNS: list[tuple[str, str]] = [
    ("bearer_token", r"Bearer\s+[a-zA-Z0-9._\-]+"),
]


def redact_text(text: str) -> str:
    """Redact API keys, tokens, and secrets from ``text``.

    Applies the SECRET_REGEXES from ``src.backend.core.redaction`` plus
    additional patterns for ``Bearer`` tokens and common key formats.
    Returns the redacted string with sensitive values replaced by
    ``[REDACTED]``.
    """
    from src.backend.core.redaction import REDACTION_PLACEHOLDER

    for _name, pattern in SECRET_REGEXES:
        text = re.sub(pattern, REDACTION_PLACEHOLDER, text)
    for _name, pattern in _EXTRA_REDACT_PATTERNS:
        text = re.sub(pattern, REDACTION_PLACEHOLDER, text)
    return text


__all__ = [
    "LLMFormatError",
    "LLMServiceError",
    "MAX_ATTEMPTS",
    "UnknownRoleError",
    "VALID_ROLES",
    "chat_completion",
    "redact_text",
    "resolve_model",
]
