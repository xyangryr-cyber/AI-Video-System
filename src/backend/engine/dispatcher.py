"""[SPEC-C-003] Dispatcher polling & single-concurrency task scheduling.

Authority: ``docs/specs/SPEC-C-backend-core.md`` SPEC-3.3.

Responsibility
--------------
One tick of the dispatcher = one ``dispatch_once()`` call. Each tick:

1. Honour single-concurrency: if any ``task_ledger`` row is currently
   in ``queued`` or ``running`` state, the concurrency slot is taken
   and the tick is a no-op.
2. Otherwise scan ``pending`` tasks in ``created_at`` order and promote
   the oldest one whose every ``depends_on`` id resolves to a
   ``succeeded`` row (``superseded`` / ``failed`` / ``timeout`` do NOT
   satisfy a dependency per SPEC-3.3).

The caller (SPEC-B Worker / run loop) owns the 2-second cadence; this
class just exposes the configurable interval so the caller can sleep
for the right amount between ticks.

The status transition is delegated to
:class:`src.backend.engine.workflow_engine.WorkflowEngine` so every
state change continues to flow through the SPEC-3.1 centralisation
point and land a ``task.queued`` event in the ``events`` table.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.backend.engine.workflow_engine import WorkflowEngine


_DEFAULT_POLLING_INTERVAL_SEC = 2.0

# States that still hold the single-concurrency slot (or would, once
# the worker picks them up). Dispatcher must not queue new work while
# any row is in one of these states.
_ACTIVE_STATUSES = ("queued", "running")


def _noop_runner(task_type: str, task_id: str, params: dict) -> None:
    """Default no-op task_runner (records nothing, does nothing)."""


class Dispatcher:
    """Polls ``task_ledger`` and promotes ready pending tasks."""

    def __init__(
        self,
        engine: "WorkflowEngine",
        polling_interval: float = _DEFAULT_POLLING_INTERVAL_SEC,
        task_runner: Callable[[str, str, dict], None] | None = _noop_runner,
    ) -> None:
        self._engine = engine
        self._polling_interval = float(polling_interval)
        self._task_runner = task_runner

    @property
    def polling_interval(self) -> float:
        """Seconds between ``dispatch_once`` calls (caller-driven)."""
        return self._polling_interval

    def dispatch_once(self) -> list[str]:
        """Run one poll cycle. Returns the ids transitioned to queued.

        Returns an empty list when (a) the concurrency slot is taken,
        or (b) no pending task has all its dependencies satisfied.
        """
        conn: sqlite3.Connection = self._engine._conn  # noqa: SLF001
        if self._slot_taken(conn):
            return []

        for (
            task_id,
            depends_on_json,
            task_type,
            params_json,
        ) in self._pending_by_created_at(conn):
            if self._deps_satisfied(conn, depends_on_json):
                self._engine.update_task_status(task_id, "queued")
                if self._task_runner is not None:
                    params_dict: dict = json.loads(params_json) if params_json else {}
                    self._task_runner(task_type, task_id, params_dict)
                return [task_id]
        return []

    # ---- Internals ---------------------------------------------------

    @staticmethod
    def _slot_taken(conn: sqlite3.Connection) -> bool:
        row = conn.execute(
            "SELECT COUNT(*) FROM task_ledger WHERE status IN ('queued','running')"
        ).fetchone()
        return bool(row and int(row[0]) > 0)

    @staticmethod
    def _pending_by_created_at(
        conn: sqlite3.Connection,
    ) -> list[tuple[str, str | None, str, str | None]]:
        rows = conn.execute(
            "SELECT id, depends_on, type, params FROM task_ledger "
            "WHERE status = 'pending' ORDER BY created_at ASC, id ASC"
        ).fetchall()
        return [(str(r[0]), r[1], str(r[2]), r[3]) for r in rows]

    @staticmethod
    def _deps_satisfied(conn: sqlite3.Connection, depends_on_json: str | None) -> bool:
        if not depends_on_json:
            return True
        try:
            dep_ids = json.loads(depends_on_json)
        except (TypeError, ValueError):
            return False
        if not isinstance(dep_ids, list) or not dep_ids:
            return True
        placeholders = ",".join("?" * len(dep_ids))
        rows = conn.execute(
            f"SELECT id, status FROM task_ledger WHERE id IN ({placeholders})",
            tuple(str(d) for d in dep_ids),
        ).fetchall()
        seen = {str(r[0]): str(r[1]) for r in rows}
        for dep_id in dep_ids:
            if seen.get(str(dep_id)) != "succeeded":
                return False
        return True


__all__ = ["Dispatcher"]
