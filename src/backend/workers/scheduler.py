"""FIFO scheduler for async_tasks (SPEC-B-004).

``pick_next`` pops the oldest pending/queued row, claims it running
via the repository, and returns the updated row. The global ordering
is owned by :class:`AsyncTaskRepository`; this module is a thin
claim wrapper so the Huey worker (SPEC-B-003) and tests share one
code path.

DB writes MUST live in the repository (SPEC-B-002 AC-4); this module
only calls repository methods.
"""

from __future__ import annotations

import sqlite3

from src.backend.db.repositories.async_task_repo import AsyncTaskRepository


def pick_next(repo: AsyncTaskRepository, worker_id: str | None = None) -> sqlite3.Row | None:
    row = repo.next_ready()
    if row is None:
        return None
    repo.mark_running(row["task_id"], worker_id=worker_id)
    return repo.get(row["task_id"])
