"""LLM client wrapper with auto-logging to agent_call_log (SPEC-B-007).

Wraps :func:`llm_service.chat_completion` so every LLM call is
automatically recorded in ``agent_call_log`` with measured duration,
token counts, and prompt/response content.
"""

from __future__ import annotations

import logging
import sqlite3
import time
from collections.abc import Callable, Mapping, Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

from src.backend.core.redaction import redact_text, truncate_large_payload
from src.backend.db.repositories.agent_call_log_repo import AgentCallLogRepository
from src.backend.services.llm_service import chat_completion as _chat_completion

log = logging.getLogger(__name__)

M = TypeVar("M", bound=BaseModel)

COST_PER_1M_TOKENS = 2.0
COST_WARN_THRESHOLD = 15.0


def _extract_tokens(response: Any) -> int:
    """Pull total_tokens from a LiteLLM-style response envelope."""
    if isinstance(response, Mapping):
        usage = response.get("usage", {})
        if isinstance(usage, Mapping):
            return int(usage.get("total_tokens", 0))
        return 0
    try:
        return int(response.usage.total_tokens)
    except (AttributeError, TypeError):
        return 0


def _extract_model(response: Any) -> str:
    if isinstance(response, Mapping):
        return str(response.get("model", "unknown"))
    try:
        return str(response.model)
    except AttributeError:
        return "unknown"


def _serialize_messages(messages: Sequence[Mapping[str, Any]]) -> str:
    """Serialize messages list to a compact string for prompt storage."""
    parts = []
    for m in messages:
        role = m.get("role", "unknown")
        content = str(m.get("content", ""))
        parts.append(f"[{role}] {content}")
    return "\n".join(parts)


def _extract_content(response: Any) -> str:
    if isinstance(response, Mapping):
        choices = response.get("choices", [])
        if choices:
            first = choices[0]
            msg = first.get("message", first) if isinstance(first, Mapping) else first.message
            content = (
                msg.get("content", "") if isinstance(msg, Mapping) else getattr(msg, "content", "")
            )
            return str(content) if content else ""
    else:
        try:
            choices = response.choices
            if choices:
                msg = choices[0].message
                return str(getattr(msg, "content", "") or "")
        except (AttributeError, IndexError):
            pass
    return ""


class LLMClient:
    """Wrapper around ``chat_completion`` that auto-logs to
    ``agent_call_log`` with measured duration, tokens, and cost check.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._repo = AgentCallLogRepository(conn)

    def chat_completion(
        self,
        *,
        role: str,
        messages: Sequence[Mapping[str, Any]],
        agent_name: str,
        phase: int | None = None,
        project_id: str | None = None,
        response_model: type[M] | None = None,
        _completion_fn: Callable[..., Any] | None = None,
        **extra: Any,
    ) -> Any:
        start = time.perf_counter()
        completion = _completion_fn if _completion_fn is not None else _chat_completion

        result = completion(
            role=role,
            messages=messages,
            response_model=response_model,
            **extra,
        )

        duration_ms = int((time.perf_counter() - start) * 1000)
        tokens = _extract_tokens(result)
        model = _extract_model(result)
        prompt_str = _serialize_messages(messages)
        response_str = _extract_content(result)

        prompt_str = truncate_large_payload(redact_text(prompt_str))
        response_str = truncate_large_payload(redact_text(response_str))

        self._repo.insert(
            agent_name=agent_name,
            tokens=tokens or 1,
            duration_ms=max(duration_ms, 1),
            phase=phase,
            project_id=project_id,
            model=model,
            prompt=prompt_str,
            response=response_str,
        )

        if project_id is not None:
            total_cost = self._repo.total_cost_for_project(project_id)
            if total_cost > COST_WARN_THRESHOLD:
                log.warning(
                    "cost_warn_at_15_dollars",
                    extra={
                        "project_id": project_id,
                        "total_cost_usd": round(total_cost, 4),
                        "threshold": COST_WARN_THRESHOLD,
                    },
                )

        return result
