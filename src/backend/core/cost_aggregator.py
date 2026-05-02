"""Cost aggregation queries for agent_call_log (SPEC-B-007)."""

from __future__ import annotations

import sqlite3

from src.backend.db.repositories.agent_call_log_repo import AgentCallLogRepository


class CostAggregator:
    """Read-only aggregator over agent_call_log for cost queries."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._repo = AgentCallLogRepository(conn)

    def total_cost_usd(self, project_id: str) -> float:
        return self._repo.total_cost_for_project(project_id)

    def by_phase(self, project_id: str) -> dict[int, float]:
        return self._repo.cost_by_phase(project_id)

    def total_tokens(self, project_id: str) -> int:
        return self._repo.project_total_tokens(project_id)
