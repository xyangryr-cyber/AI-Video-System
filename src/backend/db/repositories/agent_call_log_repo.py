"""CRUD for ``agent_call_log`` (SPEC-B-007)."""

from __future__ import annotations

from typing import cast

from src.backend.db.repositories.base import BaseRepository


class AgentCallLogRepository(BaseRepository):
    def insert(
        self,
        agent_name: str,
        tokens: int,
        duration_ms: int,
        model: str,
        prompt: str,
        response: str,
        phase: int | None = None,
        project_id: str | None = None,
    ) -> int:
        cur = self.execute(
            "INSERT INTO agent_call_log "
            "(agent_name, tokens, duration_ms, phase, project_id, model, "
            " prompt, response) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                agent_name,
                tokens,
                duration_ms,
                phase,
                project_id,
                model,
                prompt,
                response,
            ),
        )
        self.commit()
        return cast(int, cur.lastrowid)

    def total_cost_for_project(self, project_id: str) -> float:
        """Sum cost across all rows for the project. Uses $2/1M token rate."""
        row = self.execute(
            "SELECT COALESCE(SUM(tokens), 0) AS total_tokens "
            "FROM agent_call_log WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        total_tokens = row["total_tokens"] if row else 0
        return (total_tokens / 1_000_000.0) * 2.0

    def cost_by_phase(self, project_id: str) -> dict[int, float]:
        """Return {phase_num: cost_usd} for the given project."""
        rows = self.execute(
            "SELECT phase, SUM(tokens) AS total_tokens "
            "FROM agent_call_log "
            "WHERE project_id = ? "
            "GROUP BY phase",
            (project_id,),
        ).fetchall()
        result: dict[int, float] = {}
        for r in rows:
            if r["phase"] is not None:
                result[r["phase"]] = (r["total_tokens"] / 1_000_000.0) * 2.0
        return result

    def project_total_tokens(self, project_id: str) -> int:
        row = self.execute(
            "SELECT COALESCE(SUM(tokens), 0) AS n FROM agent_call_log "
            "WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        return int(row["n"]) if row else 0
