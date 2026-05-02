"""[SPEC-G-000e] Agent Call Logger — writes agent_call_log rows per HARNESS §8.1.

Every agent call MUST log: agent_name, duration_ms, token counts, model,
input_summary, output_summary, phase, project_id.

Delegates DB writes to AgentCallLogRepository (SPEC-B-002 AC-4).
"""

from __future__ import annotations

import sqlite3

from src.backend.db.repositories.agent_call_log_repo import AgentCallLogRepository


class AgentCallLogger:
    """Writes agent invocation metadata to the ``agent_call_log`` table."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._repo = AgentCallLogRepository(conn)

    def log_call(
        self,
        *,
        agent_name: str,
        duration_ms: int,
        tokens: int = 1,
        model: str = "unknown",
        input_summary: str = "",
        output_summary: str = "",
        phase: int | None = None,
        project_id: str | None = None,
    ) -> int:
        safe_tokens = max(int(tokens), 1)
        return self._repo.insert(
            agent_name=agent_name,
            tokens=safe_tokens,
            duration_ms=int(duration_ms),
            model=model,
            prompt=input_summary,
            response=output_summary,
            phase=phase,
            project_id=project_id,
        )
