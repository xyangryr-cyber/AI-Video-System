"""Tests for [SPEC-C-003] Dispatcher Polling & Task Scheduling.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.3.

Test strategy per AC (mapped from task card; real tests live here
per allowed_files, `test_spec_c_003.py` keeps its skip-stub per the
SPEC-C-001 / SPEC-C-002 precedent):

- AC-1 3 pending tasks with satisfied dependencies are dispatched in
  ``created_at`` order: seed 3 rows with explicit ascending created_at
  stamps, step the dispatcher 3 times (marking each queued task
  ``succeeded`` between steps to free the single-concurrency slot) and
  assert the emitted order matches created_at.

- AC-2 At most 1 task in ``running`` state: seed a task already in
  ``running`` + a ready pending task. One ``dispatch_once`` call must
  NOT transition the pending row (the concurrency slot is taken).

- AC-3 Polling interval configurable, defaults to 2.0s: direct
  attribute check on ``Dispatcher(engine)`` vs
  ``Dispatcher(engine, polling_interval=5.0)``.

- AC-4 Tasks with unsatisfied dependencies stay pending: seed task B
  depending on task A (still pending). ``dispatch_once`` must leave B
  in ``pending``.

- AC-5 ``superseded`` tasks are skipped: seed a ``superseded`` row and
  a ready pending row. ``dispatch_once`` must (a) not touch the
  superseded row, (b) still promote the pending row.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "src" / "backend"
SCHEMA_FILE = BACKEND_DIR / "db" / "schema.sql"


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _seed_project_and_phase(
    conn: sqlite3.Connection,
    project_id: str = "proj_c003",
    phase_num: int = 0,
) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name) VALUES(?, ?, ?)",
        (project_id, phase_num, f"P{phase_num}"),
    )
    conn.commit()


def _insert_task(
    conn: sqlite3.Connection,
    task_id: str,
    project_id: str,
    phase: int,
    task_type: str,
    status: str,
    depends_on: list[str] | None = None,
    created_at: str | None = None,
) -> None:
    """Raw insert so tests can control created_at + status precisely.

    Bypasses WorkflowEngine on purpose: the scenarios under test need
    rows that the engine's public surface (status=pending only) cannot
    produce, and the HARNESS §1 repository exemption applies to test
    fixtures (same pattern as test_workflow_engine.py seeding).
    """
    if created_at is not None:
        conn.execute(
            "INSERT INTO task_ledger("
            "id, project_id, phase, type, status, depends_on, params, "
            "created_at, updated_at) "
            "VALUES(?, ?, ?, ?, ?, ?, '{}', ?, ?)",
            (
                task_id,
                project_id,
                phase,
                task_type,
                status,
                json.dumps(depends_on) if depends_on is not None else None,
                created_at,
                created_at,
            ),
        )
    else:
        conn.execute(
            "INSERT INTO task_ledger("
            "id, project_id, phase, type, status, depends_on, params) "
            "VALUES(?, ?, ?, ?, ?, ?, '{}')",
            (
                task_id,
                project_id,
                phase,
                task_type,
                status,
                json.dumps(depends_on) if depends_on is not None else None,
            ),
        )
    conn.commit()


def _status(conn: sqlite3.Connection, task_id: str) -> str:
    row = conn.execute(
        "SELECT status FROM task_ledger WHERE id = ?", (task_id,)
    ).fetchone()
    assert row is not None, f"task {task_id} missing"
    return str(row[0])


class TestAC1DispatchOrderByCreatedAt:
    """AC-1: 3 pending tasks with satisfied deps are dispatched in
    created_at order."""

    def test_dispatch_order_by_created_at(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        # 3 ready pending tasks, ascending created_at.
        _insert_task(
            conn,
            "t_000001",
            "proj_c003",
            0,
            "generate_artifact",
            "pending",
            None,
            created_at="2026-04-22T10:00:00.000Z",
        )
        _insert_task(
            conn,
            "t_000002",
            "proj_c003",
            0,
            "generate_artifact",
            "pending",
            None,
            created_at="2026-04-22T10:00:01.000Z",
        )
        _insert_task(
            conn,
            "t_000003",
            "proj_c003",
            0,
            "generate_artifact",
            "pending",
            None,
            created_at="2026-04-22T10:00:02.000Z",
        )

        engine = WorkflowEngine(conn)
        dispatcher = Dispatcher(engine)

        dispatched: list[str] = []
        for _ in range(3):
            queued = dispatcher.dispatch_once()
            assert len(queued) == 1, (
                "single-concurrency: exactly one task per cycle when "
                f"slot free, got {queued}"
            )
            tid = queued[0]
            dispatched.append(tid)
            # Simulate worker: queued -> running -> succeeded so the
            # next cycle can dispatch the next ready task.
            engine.update_task_status(tid, "running", agent_name="x")
            engine.update_task_status(tid, "succeeded")

        assert dispatched == ["t_000001", "t_000002", "t_000003"], (
            f"expected created_at order, got {dispatched}"
        )


class TestAC2MaxOneRunningTask:
    """AC-2: dispatcher enforces at most 1 queued/running task."""

    def test_max_one_running_task(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        # One task already running (concurrency slot taken).
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
        # One ready pending task.
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
        dispatcher = Dispatcher(engine)

        queued = dispatcher.dispatch_once()

        assert queued == [], (
            f"dispatcher must not queue while a task is running (got {queued})"
        )
        assert _status(conn, "t_000002") == "pending", (
            "t_000002 must remain pending while slot is taken"
        )
        assert _status(conn, "t_000001") == "running"


class TestAC3PollingIntervalConfigurable:
    """AC-3: Polling interval configurable, defaults to 2.0s."""

    def test_polling_interval_default(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        engine = WorkflowEngine(conn)
        dispatcher = Dispatcher(engine)

        assert dispatcher.polling_interval == 2.0, (
            "default polling_interval must be 2.0 seconds (SPEC-3.3)"
        )

    def test_polling_interval_configurable(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        engine = WorkflowEngine(conn)

        dispatcher = Dispatcher(engine, polling_interval=5.0)

        assert dispatcher.polling_interval == 5.0


class TestAC4UnsatisfiedDepsStayPending:
    """AC-4: Tasks with unsatisfied dependencies remain pending."""

    def test_unsatisfied_deps_stay_pending(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        # Dependency A is still pending.
        _insert_task(
            conn,
            "t_000001",
            "proj_c003",
            0,
            "generate_artifact",
            "pending",
            None,
            created_at="2026-04-22T10:00:00.000Z",
        )
        # Task B depends on A.
        _insert_task(
            conn,
            "t_000002",
            "proj_c003",
            0,
            "generate_artifact",
            "pending",
            depends_on=["t_000001"],
            created_at="2026-04-22T10:00:01.000Z",
        )

        engine = WorkflowEngine(conn)
        dispatcher = Dispatcher(engine)

        queued = dispatcher.dispatch_once()

        # Only t_000001 (no deps) is ready. t_000002 must stay pending.
        assert queued == ["t_000001"]
        assert _status(conn, "t_000001") == "queued"
        assert _status(conn, "t_000002") == "pending", (
            "t_000002 has unsatisfied dep on t_000001; must stay pending"
        )

    def test_failed_dep_does_not_satisfy(self) -> None:
        """A ``failed`` predecessor does NOT satisfy the dependency
        (only ``succeeded`` does, per SPEC-3.3)."""
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
            "failed",
            None,
            created_at="2026-04-22T10:00:00.000Z",
        )
        _insert_task(
            conn,
            "t_000002",
            "proj_c003",
            0,
            "generate_artifact",
            "pending",
            depends_on=["t_000001"],
            created_at="2026-04-22T10:00:01.000Z",
        )

        engine = WorkflowEngine(conn)
        dispatcher = Dispatcher(engine)

        queued = dispatcher.dispatch_once()

        assert queued == []
        assert _status(conn, "t_000002") == "pending"


class TestAC5SupersededTasksSkipped:
    """AC-5: ``superseded`` tasks are skipped by Dispatcher."""

    def test_superseded_tasks_skipped(self) -> None:
        from src.backend.engine.dispatcher import Dispatcher
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        # Older superseded review (should be ignored by dispatcher).
        _insert_task(
            conn,
            "t_000001",
            "proj_c003",
            0,
            "review",
            "superseded",
            None,
            created_at="2026-04-22T09:00:00.000Z",
        )
        # Newer ready pending task.
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
        dispatcher = Dispatcher(engine)

        queued = dispatcher.dispatch_once()

        assert queued == ["t_000002"], (
            f"superseded tasks must not block dispatch; got {queued}"
        )
        assert _status(conn, "t_000001") == "superseded", (
            "superseded row must remain superseded (terminal state)"
        )
        assert _status(conn, "t_000002") == "queued"
