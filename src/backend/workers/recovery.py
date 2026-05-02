"""Worker crash recovery (SPEC-B-005).

Called at worker startup and periodically by the scheduler. Finds rows
stuck in ``status='running'`` whose ``started_at`` is older than the
per-type stale threshold, then either:

* re-queues the task (``attempt += 1``) if attempts remain, or
* marks it ``failed`` once ``attempt >= max_attempts``.

Returns the two ID lists so operators / tests can audit what the sweep
did. The function is idempotent: running it twice on the same DB with
the same ``stale_before`` value reprocesses no rows.
"""

from __future__ import annotations

import sqlite3
from typing import TypedDict

from src.backend.db.repositories.async_task_repo import (
    AsyncTaskRepository,
)


class RecoveryResult(TypedDict):
    requeued: list[str]
    failed: list[str]


_TIMEOUT_ERROR = "worker_timeout: stale heartbeat, retries exhausted"


def recover_orphans(
    conn: sqlite3.Connection,
    stale_before: str,
) -> RecoveryResult:
    """Sweep orphan ``running`` tasks.

    Args:
        conn: Open SQLite connection backing ``async_tasks``.
        stale_before: ISO-8601 UTC cutoff; tasks whose ``started_at``
            is strictly less than this are considered orphaned.

    Returns:
        ``{"requeued": [...], "failed": [...]}`` with one list of IDs
        per terminal transition.
    """
    repo = AsyncTaskRepository(conn)
    requeued: list[str] = []
    failed: list[str] = []
    for row in repo.list_stale_running(stale_before):
        task_id = row["task_id"]
        attempt = int(row["attempt"])
        max_attempts = int(row["max_attempts"])
        if attempt + 1 > max_attempts:
            repo.mark_failed(task_id, _TIMEOUT_ERROR)
            failed.append(task_id)
        else:
            repo.requeue_after_crash(task_id)
            requeued.append(task_id)
    return {"requeued": requeued, "failed": failed}
