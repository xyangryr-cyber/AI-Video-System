"""Tests for [SPEC-B-004] async_tasks Table + Task CRUD API.

Strategy:

* AC-1 asserts the baseline DDL carries every column SPEC-A SPEC-1B
  and SPEC-10.2 mandate. Schema file is the source of truth.
* AC-2 seeds with an in-memory sqlite DB and verifies the NOT NULL
  defaults actually stamp ``attempt=1`` / ``max_attempts=3``.
* AC-3 / AC-6 exercise ``AsyncTaskRepository`` + ``scheduler.pick_next``
  across two projects to prove the queue is global and FIFO by
  ``created_at``.
* AC-4 hits ``GET /api/projects/{id}/tasks`` via FastAPI TestClient
  wired to an in-memory DB dependency.
* AC-5 checks each queued row's ``position`` in that response equals
  the count of earlier queued/running rows globally (0-based).
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

REQUIRED_COLUMNS = (
    "task_id",
    "project_id",
    "phase",
    "ledger_task_id",
    "type",
    "params",
    "status",
    "progress",
    "worker_id",
    "attempt",
    "max_attempts",
    "started_at",
    "finished_at",
    "error",
    "created_at",
)


# ---- fixtures --------------------------------------------------------------


@pytest.fixture
def conn() -> sqlite3.Connection:
    # ``check_same_thread=False`` lets FastAPI TestClient (which runs
    # the app on a worker thread) share the same in-memory DB the test
    # body seeded on the main thread.
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    c.execute(
        "INSERT INTO projects(project_id, title, description) VALUES (?, ?, ?)",
        ("proj_a", "A", "d"),
    )
    c.execute(
        "INSERT INTO projects(project_id, title, description) VALUES (?, ?, ?)",
        ("proj_b", "B", "d"),
    )
    c.commit()
    return c


# ---- AC-1 ------------------------------------------------------------------


class TestAC1AsyncTasksTableSchema:
    """AC-1: async_tasks DDL matches SPEC-1B."""

    def test_async_tasks_ddl_present(self):
        text = SCHEMA_FILE.read_text(encoding="utf-8")
        assert re.search(r"CREATE TABLE\s+async_tasks\s*\(", text), (
            "async_tasks DDL missing from schema.sql"
        )

    def test_async_tasks_has_all_required_columns(self, conn):
        cols = {row["name"] for row in conn.execute("PRAGMA table_info(async_tasks)")}
        missing = [c for c in REQUIRED_COLUMNS if c not in cols]
        assert not missing, f"async_tasks missing columns: {missing}"


# ---- AC-2 ------------------------------------------------------------------


class TestAC2AttemptStartsAt1MaxAttemptsDefault3:
    """AC-2: attempt defaults to 1, max_attempts defaults to 3."""

    def test_defaults_come_from_schema_inserts(self, conn):
        from src.backend.db.repositories.async_task_repo import (
            AsyncTaskRepository,
        )

        repo = AsyncTaskRepository(conn)
        task_id = repo.create(
            project_id="proj_a",
            phase=4,
            type="tts",
            params={"voice": "narrator"},
        )
        row = conn.execute(
            "SELECT attempt, max_attempts FROM async_tasks WHERE task_id = ?",
            (task_id,),
        ).fetchone()
        assert row["attempt"] == 1
        assert row["max_attempts"] == 3


# ---- AC-3 + AC-6 -----------------------------------------------------------


class TestAC3FifoSchedulingAcrossProjects:
    """AC-3: FIFO by created_at across projects."""

    def test_pick_next_returns_oldest_across_projects(self, conn):
        from src.backend.db.repositories.async_task_repo import (
            AsyncTaskRepository,
        )
        from src.backend.workers.scheduler import pick_next

        repo = AsyncTaskRepository(conn)
        first = repo.create(
            project_id="proj_a",
            phase=4,
            type="tts",
            params={},
            created_at="2026-04-20T10:00:00.000Z",
        )
        second = repo.create(
            project_id="proj_b",
            phase=4,
            type="tts",
            params={},
            created_at="2026-04-20T10:00:01.000Z",
        )
        third = repo.create(
            project_id="proj_a",
            phase=4,
            type="keyframe",
            params={},
            created_at="2026-04-20T10:00:02.000Z",
        )

        picked = [pick_next(repo), pick_next(repo), pick_next(repo)]
        ids = [p["task_id"] for p in picked]
        assert ids == [first, second, third], (
            f"Scheduler must return tasks in global created_at order, got {ids}"
        )


class TestAC6SharedQueueAcrossProjects:
    """AC-6: one queue spans all projects."""

    def test_list_global_queue_contains_tasks_from_all_projects(self, conn):
        from src.backend.db.repositories.async_task_repo import (
            AsyncTaskRepository,
        )

        repo = AsyncTaskRepository(conn)
        repo.create(
            project_id="proj_a",
            phase=4,
            type="tts",
            params={},
            created_at="2026-04-20T10:00:00.000Z",
        )
        repo.create(
            project_id="proj_b",
            phase=4,
            type="tts",
            params={},
            created_at="2026-04-20T10:00:01.000Z",
        )

        tasks = repo.list_global_queue()
        project_ids = {t["project_id"] for t in tasks}
        assert project_ids == {"proj_a", "proj_b"}, (
            f"Queue must span both projects; got {project_ids}"
        )


# ---- AC-4 + AC-5 -----------------------------------------------------------


class TestAC4GetProjectTasksApi:
    """AC-4: GET /api/projects/{id}/tasks returns the project's tasks."""

    def test_endpoint_returns_project_scoped_task_list(self, conn):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from src.backend.api.routes.tasks import get_db, router
        from src.backend.db.repositories.async_task_repo import (
            AsyncTaskRepository,
        )

        repo = AsyncTaskRepository(conn)
        a1 = repo.create(
            project_id="proj_a",
            phase=4,
            type="tts",
            params={},
            created_at="2026-04-20T10:00:00.000Z",
        )
        _b1 = repo.create(
            project_id="proj_b",
            phase=4,
            type="tts",
            params={},
            created_at="2026-04-20T10:00:01.000Z",
        )
        a2 = repo.create(
            project_id="proj_a",
            phase=4,
            type="keyframe",
            params={},
            created_at="2026-04-20T10:00:02.000Z",
        )

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: conn
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/api/projects/proj_a/tasks")
        assert resp.status_code == 200, resp.text
        body = resp.json()
        assert "tasks" in body, f"expected 'tasks' key, got {list(body)}"
        ids = [t["task_id"] for t in body["tasks"]]
        assert ids == [a1, a2], (
            f"response must only include proj_a tasks in FIFO order, got {ids}"
        )


class TestAC5QueuedTaskShowsPosition:
    """AC-5: queued tasks carry a position = N-earlier in global queue."""

    def test_position_counts_earlier_queued_or_running(self, conn):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from src.backend.api.routes.tasks import get_db, router
        from src.backend.db.repositories.async_task_repo import (
            AsyncTaskRepository,
        )

        repo = AsyncTaskRepository(conn)
        # Mix of statuses: queued (positions 0, 1, 2), running in front,
        # and a finished one that must NOT count.
        running = repo.create(
            project_id="proj_b",
            phase=4,
            type="tts",
            params={},
            created_at="2026-04-20T10:00:00.000Z",
        )
        repo.update_status(running, "running")
        finished = repo.create(
            project_id="proj_b",
            phase=4,
            type="tts",
            params={},
            created_at="2026-04-20T10:00:01.000Z",
        )
        repo.update_status(finished, "succeeded")
        a1 = repo.create(
            project_id="proj_a",
            phase=4,
            type="tts",
            params={},
            created_at="2026-04-20T10:00:02.000Z",
        )
        repo.update_status(a1, "queued")
        a2 = repo.create(
            project_id="proj_a",
            phase=4,
            type="keyframe",
            params={},
            created_at="2026-04-20T10:00:03.000Z",
        )
        repo.update_status(a2, "queued")

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: conn
        app.include_router(router)
        client = TestClient(app)
        resp = client.get("/api/projects/proj_a/tasks")
        body = resp.json()
        tasks_by_id = {t["task_id"]: t for t in body["tasks"]}

        # Global queued/running sequence by created_at:
        # running -> a1 -> a2 (the 'succeeded' row is excluded).
        assert tasks_by_id[a1]["position"] == 1, (
            f"a1 expected position 1 (1 running ahead), "
            f"got {tasks_by_id[a1]['position']}"
        )
        assert tasks_by_id[a2]["position"] == 2, (
            f"a2 expected position 2, got {tasks_by_id[a2]['position']}"
        )
        assert tasks_by_id[a1]["status"] == "queued"
