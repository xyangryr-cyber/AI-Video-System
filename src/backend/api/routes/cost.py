"""GET /api/projects/{project_id}/costs (SPEC-B-007).

Returns total and per-phase LLM cost for a project.
"""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.backend.core.cost_aggregator import CostAggregator

router = APIRouter(prefix="/api", tags=["cost"])


def get_db() -> sqlite3.Connection:  # pragma: no cover -- app wiring
    raise RuntimeError("DB dependency not wired. Override get_db in tests.")


@router.get("/projects/{project_id}/costs")
def get_project_cost(
    project_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    cur = db.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="project not found")

    agg = CostAggregator(db)
    total = agg.total_cost_usd(project_id)
    by_phase = agg.by_phase(project_id)
    total_tokens = agg.total_tokens(project_id)

    return {
        "project_id": project_id,
        "total_cost_usd": round(total, 6),
        "by_phase": {str(k): round(v, 6) for k, v in by_phase.items()},
        "total_tokens": total_tokens,
        "rate_per_1m_tokens": 2.0,
    }
