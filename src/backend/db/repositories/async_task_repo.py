"""CRUD for ``async_tasks`` (SPEC-B-004).

The queue is global (no per-project partition, AC-6). Ordering is
FIFO by ``created_at`` ASC, with ``task_id`` as a stable tiebreaker.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from typing import Any, cast

from src.backend.db.repositories.base import BaseRepository


class AsyncTaskRepository(BaseRepository):
    def create(
        self,
        project_id: str,
        phase: int,
        type: str,
        params: dict[str, Any] | None = None,
        ledger_task_id: str | None = None,
        max_attempts: int = 3,
        created_at: str | None = None,
    ) -> str:
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        params_json = json.dumps(params or {}, sort_keys=True)
        if created_at is None:
            self.execute(
                "INSERT INTO async_tasks "
                "(task_id, project_id, phase, ledger_task_id, type, "
                " params, max_attempts) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    project_id,
                    phase,
                    ledger_task_id,
                    type,
                    params_json,
                    max_attempts,
                ),
            )
        else:
            self.execute(
                "INSERT INTO async_tasks "
                "(task_id, project_id, phase, ledger_task_id, type, "
                " params, max_attempts, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    task_id,
                    project_id,
                    phase,
                    ledger_task_id,
                    type,
                    params_json,
                    max_attempts,
                    created_at,
                ),
            )
        self.commit()
        return task_id

    def update_status(self, task_id: str, status: str) -> None:
        self.execute(
            "UPDATE async_tasks SET status = ? WHERE task_id = ?",
            (status, task_id),
        )
        self.commit()

    def mark_running(self, task_id: str, worker_id: str | None = None) -> None:
        """Claim a task: status=running, stamp worker + started_at."""
        self.execute(
            "UPDATE async_tasks SET status = 'running', "
            "worker_id = ?, "
            "started_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE task_id = ?",
            (worker_id, task_id),
        )
        self.commit()

    def get(self, task_id: str) -> sqlite3.Row | None:
        cur = self.execute(
            "SELECT * FROM async_tasks WHERE task_id = ?",
            (task_id,),
        )
        return cast(sqlite3.Row | None, cur.fetchone())

    def list_global_queue(self) -> list[sqlite3.Row]:
        """All tasks (any project, any status) in FIFO order."""
        cur = self.execute(
            "SELECT * FROM async_tasks ORDER BY created_at ASC, task_id ASC",
        )
        return list(cur.fetchall())

    def list_for_project(self, project_id: str) -> list[sqlite3.Row]:
        cur = self.execute(
            "SELECT * FROM async_tasks WHERE project_id = ? ORDER BY created_at ASC, task_id ASC",
            (project_id,),
        )
        return list(cur.fetchall())

    def count_ahead(self, task_id: str) -> int:
        """Number of queued/running tasks strictly older than
        ``task_id`` across all projects (0-based position).
        """
        row = self.execute(
            "SELECT created_at FROM async_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        if row is None:
            raise KeyError(task_id)
        cur = self.execute(
            "SELECT COUNT(*) AS n FROM async_tasks "
            "WHERE status IN ('queued', 'running') "
            "AND (created_at, task_id) < (?, ?)",
            (row["created_at"], task_id),
        )
        return int(cur.fetchone()["n"])

    def next_ready(self) -> sqlite3.Row | None:
        """Oldest ``pending`` / ``queued`` task globally, or None."""
        cur = self.execute(
            "SELECT * FROM async_tasks "
            "WHERE status IN ('pending', 'queued') "
            "ORDER BY created_at ASC, task_id ASC "
            "LIMIT 1"
        )
        return cast(sqlite3.Row | None, cur.fetchone())

    # ---- SPEC-B-005: crash recovery + cancel optimistic lock ----------

    def list_stale_running(self, stale_before: str) -> list[sqlite3.Row]:
        """Rows with ``status='running'`` and ``started_at < stale_before``.

        Orphan detection for worker-crash recovery. ``stale_before`` is
        an ISO-8601 UTC timestamp (same format as ``started_at``); the
        caller decides the threshold from
        ``huey_config.stale_threshold_for(task_type)``.
        """
        cur = self.execute(
            "SELECT * FROM async_tasks "
            "WHERE status = 'running' "
            "AND started_at IS NOT NULL "
            "AND started_at < ? "
            "ORDER BY started_at ASC",
            (stale_before,),
        )
        return list(cur.fetchall())

    def requeue_after_crash(self, task_id: str) -> None:
        """Flip a stale ``running`` task back to ``queued`` and bump
        ``attempt``. Caller is responsible for having already checked
        ``attempt < max_attempts`` -- use :func:`recover_orphans` for
        the complete decision."""
        self.execute(
            "UPDATE async_tasks "
            "SET status = 'queued', "
            "    attempt = attempt + 1, "
            "    worker_id = NULL, "
            "    started_at = NULL "
            "WHERE task_id = ? AND status = 'running'",
            (task_id,),
        )
        self.commit()

    def mark_failed(self, task_id: str, error: str) -> None:
        """Terminal ``failed`` state. Stamps ``finished_at`` and
        stores the failure reason for audit."""
        self.execute(
            "UPDATE async_tasks "
            "SET status = 'failed', "
            "    error = ?, "
            "    finished_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE task_id = ?",
            (error, task_id),
        )
        self.commit()

    def cancel(self, task_id: str) -> int:
        """Optimistic-locked cancel. Only transitions ``running`` /
        ``queued`` / ``pending`` rows to ``cancelled``; returns the
        ``UPDATE`` rowcount so callers can detect races where the
        worker already finished the task.
        """
        cur = self.execute(
            "UPDATE async_tasks "
            "SET status = 'cancelled', "
            "    finished_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE task_id = ? "
            "AND status IN ('pending', 'queued', 'running')",
            (task_id,),
        )
        self.commit()
        return int(cur.rowcount)
