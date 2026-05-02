"""GET /api/projects/{project_id}/tasks (SPEC-B-004).

Returns the project-scoped slice of the global async-task queue.
Each item carries a ``position`` = count of earlier queued/running
tasks across ALL projects (0-based); finished/cancelled rows do not
count.
"""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.backend.db.repositories.async_task_repo import AsyncTaskRepository

router = APIRouter(prefix="/api", tags=["tasks"])


def get_db() -> sqlite3.Connection:  # pragma: no cover -- app wiring
    """Overridden via ``app.dependency_overrides[get_db]`` in tests
    and by the production startup hook in a later SPEC-B task.
    """
    raise RuntimeError(
        "DB dependency not wired. Override get_db in the app startup hook or in tests."
    )


def _serialize(row: sqlite3.Row, position: int) -> dict[str, Any]:
    try:
        params = json.loads(row["params"]) if row["params"] else {}
    except (ValueError, TypeError):
        params = {}
    return {
        "task_id": row["task_id"],
        "project_id": row["project_id"],
        "phase": row["phase"],
        "ledger_task_id": row["ledger_task_id"],
        "type": row["type"],
        "params": params,
        "status": row["status"],
        "progress": row["progress"],
        "worker_id": row["worker_id"],
        "attempt": row["attempt"],
        "max_attempts": row["max_attempts"],
        "started_at": row["started_at"],
        "finished_at": row["finished_at"],
        "error": row["error"],
        "created_at": row["created_at"],
        "position": position,
    }


@router.get("/projects/{project_id}/tasks")
def list_project_tasks(
    project_id: str,
    phase: int | None = None,
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    repo = AsyncTaskRepository(db)
    # Sanity: require project row to exist so a typo surfaces as 404.
    cur = db.execute("SELECT 1 FROM projects WHERE project_id = ?", (project_id,))
    if cur.fetchone() is None:
        raise HTTPException(status_code=404, detail="project not found")

    rows = repo.list_for_project(project_id)
    if phase is not None:
        rows = [r for r in rows if r["phase"] == phase]
    tasks = [_serialize(r, repo.count_ahead(r["task_id"])) for r in rows]

    # Find current task: first "running", else first "queued", else None
    current_task = None
    for t in tasks:
        if t["status"] in ("running", "queued"):
            current_task = {"id": t["task_id"], "type": t["type"], "status": t["status"]}
            break

    return {"project_id": project_id, "tasks": tasks, "current_task": current_task}
