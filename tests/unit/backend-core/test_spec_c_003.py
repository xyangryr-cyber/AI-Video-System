"""Tests for [SPEC-C-003] Dispatcher Polling & Task Scheduling.

Canonical discovery point. Real test classes live in
``test_dispatcher.py`` for AC-1 through AC-5 and are re-exported here.
AC-6 through AC-8 (SPEC-G-000a task_runner injection) live here directly
per allowed_files constraint.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock

from importlib.machinery import SourceFileLoader

_dir = Path(__file__).parent

# Re-export AC-1 through AC-5 from test_dispatcher.py.
_disp = SourceFileLoader(
    "test_dispatcher", str(_dir / "test_dispatcher.py")
).load_module()

# Pull in shared helpers from test_dispatcher.
_seed_schema = _disp._seed_schema
_seed_project_and_phase = _disp._seed_project_and_phase
_insert_task = _disp._insert_task
_status = _disp._status


class TestAC1DispatchOrderByCreatedAt(_disp.TestAC1DispatchOrderByCreatedAt):
    pass


class TestAC2MaxOneRunningTask(_disp.TestAC2MaxOneRunningTask):
    pass


class TestAC3PollingIntervalConfigurable(_disp.TestAC3PollingIntervalConfigurable):
    pass


class TestAC4UnsatisfiedDepsStayPending(_disp.TestAC4UnsatisfiedDepsStayPending):
    pass


class TestAC5SupersededTasksSkipped(_disp.TestAC5SupersededTasksSkipped):
    pass


# ---------------------------------------------------------------------------
# [SPEC-G-000a] task_runner injection tests (AC-6, AC-7, AC-8)
# ---------------------------------------------------------------------------


def _insert_task_with_params(
    conn: sqlite3.Connection,
    task_id: str,
    project_id: str,
    phase: int,
    task_type: str,
    status: str,
    depends_on: list[str] | None = None,
    created_at: str | None = None,
    params: dict | None = None,
) -> None:
    """Like _insert_task but allows custom ``params`` dict."""
    if created_at is not None:
        conn.execute(
            "INSERT INTO task_ledger("
            "id, project_id, phase, type, status, depends_on, params, "
            "created_at, updated_at) "
            "VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                task_id,
                project_id,
                phase,
                task_type,
                status,
                json.dumps(depends_on) if depends_on is not None else None,
                json.dumps(params) if params is not None else "{}",
                created_at,
                created_at,
            ),
        )
    else:
        conn.execute(
            "INSERT INTO task_ledger("
            "id, project_id, phase, type, status, depends_on, params) "
            "VALUES(?, ?, ?, ?, ?, ?, ?)",
            (
                task_id,
                project_id,
                phase,
                task_type,
                status,
                json.dumps(depends_on) if depends_on is not None else None,
                json.dumps(params) if params is not None else "{}",
            ),
        )
    conn.commit()


class TestAC6DispatchCallsRunnerOnPromote:
    """AC-6: task_runner is called after promote with correct args."""

    def test_dispatch_calls_runner_on_promote(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        _insert_task_with_params(
            conn,
            "t_000001",
            "proj_c003",
            0,
            "generate_artifact",
            "pending",
            None,
            created_at="2026-04-22T10:00:00.000Z",
            params={"key": "value"},
        )

        engine = WorkflowEngine(conn)
        mock_runner = MagicMock()
        dispatcher = Dispatcher(engine, task_runner=mock_runner)

        queued = dispatcher.dispatch_once()

        assert queued == ["t_000001"]
        mock_runner.assert_called_once_with(
            "generate_artifact", "t_000001", {"key": "value"}
        )


class TestAC7DispatchSkipsRunnerWhenSlotTaken:
    """AC-7: task_runner is NOT called when concurrency slot is taken."""

    def test_dispatch_skips_runner_when_slot_taken(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        _insert_task(
            conn,
            "t_000001",
            "proj_c003",
            0,
            "generate_artifact",
            "running",
            None,
            created_at="2026-04-22T09:00:00.000Z",
        )
        _insert_task(
            conn,
            "t_000002",
            "proj_c003",
            0,
            "generate_artifact",
            "pending",
            None,
            created_at="2026-04-22T10:00:00.000Z",
        )

        engine = WorkflowEngine(conn)
        mock_runner = MagicMock()
        dispatcher = Dispatcher(engine, task_runner=mock_runner)

        queued = dispatcher.dispatch_once()

        assert queued == []
        mock_runner.assert_not_called()


class TestAC8DispatchSkipsRunnerWhenDepsUnmet:
    """AC-8: task_runner is NOT called when no task has satisfied deps."""

    def test_dispatch_skips_runner_when_deps_unmet(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        # A single pending task whose only dependency does not exist
        # (and therefore cannot be "succeeded").
        _insert_task(
            conn,
            "t_000001",
            "proj_c003",
            0,
            "generate_artifact",
            "pending",
            depends_on=["t_missing"],
            created_at="2026-04-22T10:00:00.000Z",
        )

        engine = WorkflowEngine(conn)
        mock_runner = MagicMock()
        dispatcher = Dispatcher(engine, task_runner=mock_runner)

        queued = dispatcher.dispatch_once()

        assert queued == []
        mock_runner.assert_not_called()
