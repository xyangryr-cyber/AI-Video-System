"""Tests for [SPEC-B-005] Worker Crash Recovery + Browser Disconnect.

Strategy:

* AC-1 seeds a task with ``status=running`` and ``started_at`` well past
  the stale threshold, then calls ``recover_orphans`` -- the row must
  flip to ``queued`` with ``attempt`` incremented by 1.
* AC-2 seeds two stale-running rows and one fresh-running row and asserts
  ``list_stale_running`` returns only the stale ones (orphan detection).
* AC-3 seeds a stale-running row with ``attempt == max_attempts`` and
  asserts ``recover_orphans`` marks it ``failed`` (no further retry).
* AC-4 exercises ``cancel`` against a row already ``succeeded`` to prove
  the ``WHERE status IN ('running','queued')`` optimistic guard short-
  circuits the race; a second assertion verifies the SQL literal.
* AC-5 statically inspects ``src/backend/workers/run.py`` and
  ``huey_config.py`` for forbidden frontend imports -- the worker must
  stay a headless process, independent of browser lifecycle.
* AC-6 mutates ``progress``/``status`` on the row and asserts the task
  API reads the new values from the DB (no stale local cache), proving
  a reconnecting browser gets authoritative state.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"
WORKER_RUN_FILE = REPO_ROOT / "src" / "backend" / "workers" / "run.py"
WORKER_HUEY_FILE = REPO_ROOT / "src" / "backend" / "workers" / "huey_config.py"
REPO_FILE = REPO_ROOT / "src" / "backend" / "db" / "repositories" / "async_task_repo.py"


# ---- fixtures --------------------------------------------------------------


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    c.execute(
        "INSERT INTO projects(project_id, title, description) VALUES (?, ?, ?)",
        ("proj_a", "A", "d"),
    )
    c.commit()
    return c


def _seed_running(
    conn: sqlite3.Connection,
    task_id: str,
    *,
    started_at: str,
    attempt: int = 1,
    max_attempts: int = 3,
    created_at: str = "2026-04-20T10:00:00.000Z",
) -> None:
    """Insert a task directly in ``running`` state with a specific
    ``started_at`` so tests can control staleness."""
    conn.execute(
        "INSERT INTO async_tasks "
        "(task_id, project_id, phase, type, params, status, "
        " attempt, max_attempts, worker_id, started_at, created_at) "
        "VALUES (?, 'proj_a', 4, 'tts', '{}', 'running', "
        " ?, ?, 'worker-1', ?, ?)",
        (task_id, attempt, max_attempts, started_at, created_at),
    )
    conn.commit()


# ---- AC-1 ------------------------------------------------------------------


class TestAC1RetryAppearsAfterKill:
    """AC-1: kill -9 Worker 后 35-95s 出现 status=queued, attempt+1."""

    def test_retry_appears_after_kill(self, conn):
        from src.backend.workers.recovery import recover_orphans

        _seed_running(
            conn,
            "task_killed",
            started_at="2026-04-20T09:00:00.000Z",
            attempt=1,
        )

        # Stale threshold is 10:00:00; the seeded row started at 09:00:00
        # (60 min earlier) -- well past any per-type timeout + 60s grace.
        result = recover_orphans(conn, stale_before="2026-04-20T10:00:00.000Z")

        row = conn.execute(
            "SELECT status, attempt FROM async_tasks WHERE task_id = 'task_killed'"
        ).fetchone()
        assert row["status"] == "queued", (
            f"expected status=queued after stale-recovery, got {row['status']}"
        )
        assert row["attempt"] == 2, (
            f"expected attempt incremented to 2, got {row['attempt']}"
        )
        assert "task_killed" in result["requeued"], (
            f"task_killed must appear in requeued list, got {result}"
        )


# ---- AC-2 ------------------------------------------------------------------


class TestAC2OrphanTaskRecoveryOnRestart:
    """AC-2: Worker 重启后孤儿任务被检测并恢复。"""

    def test_orphan_task_recovery_on_restart(self, conn):
        from src.backend.db.repositories.async_task_repo import (
            AsyncTaskRepository,
        )

        # Two orphans (started 09:00 / 09:30) + one fresh (started 09:59:55).
        _seed_running(
            conn,
            "task_orphan_a",
            started_at="2026-04-20T09:00:00.000Z",
        )
        _seed_running(
            conn,
            "task_orphan_b",
            started_at="2026-04-20T09:30:00.000Z",
            created_at="2026-04-20T10:00:01.000Z",
        )
        _seed_running(
            conn,
            "task_fresh",
            started_at="2026-04-20T09:59:55.000Z",
            created_at="2026-04-20T10:00:02.000Z",
        )

        repo = AsyncTaskRepository(conn)
        stale = repo.list_stale_running(stale_before="2026-04-20T09:58:00.000Z")
        stale_ids = {r["task_id"] for r in stale}
        assert stale_ids == {"task_orphan_a", "task_orphan_b"}, (
            f"orphan detection must include stale running tasks and "
            f"exclude fresh ones; got {stale_ids}"
        )


# ---- AC-3 ------------------------------------------------------------------


class TestAC3MaxAttemptsExceededMarksFailed:
    """AC-3: attempt >= max_attempts 时任务置为 failed，不再重试。"""

    def test_max_attempts_exceeded_marks_failed(self, conn):
        from src.backend.workers.recovery import recover_orphans

        _seed_running(
            conn,
            "task_exhausted",
            started_at="2026-04-20T09:00:00.000Z",
            attempt=3,
            max_attempts=3,
        )

        result = recover_orphans(conn, stale_before="2026-04-20T10:00:00.000Z")

        row = conn.execute(
            "SELECT status, finished_at, error "
            "FROM async_tasks WHERE task_id = 'task_exhausted'"
        ).fetchone()
        assert row["status"] == "failed", (
            f"attempt==max_attempts must flip to failed on stale-recovery, "
            f"got {row['status']}"
        )
        assert row["finished_at"] is not None, (
            "failed terminal state must stamp finished_at"
        )
        assert row["error"], (
            "failed terminal state must record a non-empty error reason"
        )
        assert "task_exhausted" in result["failed"], (
            f"task_exhausted must appear in failed list, got {result}"
        )
        assert "task_exhausted" not in result["requeued"], (
            "exhausted task must NOT be requeued"
        )


# ---- AC-4 ------------------------------------------------------------------


class TestAC4OptimisticLockPreventsCancelRace:
    """AC-4: 乐观锁 WHERE status IN (running, queued) 防止 cancel 竞态。"""

    def test_cancel_noops_when_already_terminal(self, conn):
        from src.backend.db.repositories.async_task_repo import (
            AsyncTaskRepository,
        )

        # Race: worker already succeeded the task before user clicks cancel.
        conn.execute(
            "INSERT INTO async_tasks "
            "(task_id, project_id, phase, type, params, status) "
            "VALUES "
            "('task_done', 'proj_a', 4, 'tts', '{}', 'succeeded')"
        )
        conn.commit()

        repo = AsyncTaskRepository(conn)
        rowcount = repo.cancel("task_done")
        assert rowcount == 0, (
            f"cancel against a succeeded task must be a no-op "
            f"(optimistic lock); got rowcount={rowcount}"
        )
        row = conn.execute(
            "SELECT status FROM async_tasks WHERE task_id = 'task_done'"
        ).fetchone()
        assert row["status"] == "succeeded", (
            f"terminal status must be preserved, got {row['status']}"
        )

    def test_cancel_succeeds_when_running_or_queued(self, conn):
        from src.backend.db.repositories.async_task_repo import (
            AsyncTaskRepository,
        )

        conn.execute(
            "INSERT INTO async_tasks "
            "(task_id, project_id, phase, type, params, status) "
            "VALUES "
            "('task_active', 'proj_a', 4, 'tts', '{}', 'running')"
        )
        conn.commit()

        repo = AsyncTaskRepository(conn)
        rowcount = repo.cancel("task_active")
        assert rowcount == 1
        row = conn.execute(
            "SELECT status FROM async_tasks WHERE task_id = 'task_active'"
        ).fetchone()
        assert row["status"] == "cancelled"

    def test_cancel_sql_contains_status_in_guard(self):
        """Mechanical guard: the optimistic lock predicate is the
        literal SPEC requires. Task card verification_commands greps
        for this exact string. We require the predicate to appear in
        the same statement as ``SET status = 'cancelled'`` so a generic
        ``count_ahead`` SELECT doesn't satisfy this check."""
        text = REPO_FILE.read_text(encoding="utf-8")
        # Greedy but single-statement: from SET status='cancelled' up to
        # the next semicolon or closing quote, must contain status IN(..).
        cancel_block = re.search(
            r"SET\s+status\s*=\s*'cancelled'[\s\S]{0,400}?"
            r"WHERE[\s\S]{0,200}?status\s+IN\s*\(",
            text,
        )
        assert cancel_block, (
            "async_task_repo.py must contain an UPDATE that sets "
            "status='cancelled' AND guards with WHERE status IN (...) "
            "in the same statement"
        )


# ---- AC-5 ------------------------------------------------------------------


class TestAC5WorkerSurvivesBrowserClose:
    """AC-5: Worker 运行不依赖浏览器/前端状态，重启时自动恢复孤儿任务。

    The operational behavior "worker survives browser close" has two
    invariants the unit layer can enforce:

    1. The worker entrypoint module stays headless (no HTTP / WS imports).
    2. The entrypoint wires :func:`recover_orphans` into startup so that
       a worker process surviving a browser disconnect can still clean
       up the tasks a *previous* crash left in ``running`` state. This is
       the load-bearing NEW behavior SPEC-B-005 introduces.
    """

    def test_worker_run_wires_orphan_recovery_on_startup(self):
        text = WORKER_RUN_FILE.read_text(encoding="utf-8")
        assert "recover_orphans" in text, (
            "run.py must import and call recover_orphans on startup so "
            "a restarting worker sweeps orphan running-tasks from the "
            "previous crash"
        )
        # Must actually be invoked, not just imported.
        assert re.search(r"recover_orphans\s*\(", text), (
            "run.py must CALL recover_orphans(...) during main(), not just import it"
        )

    def test_worker_run_has_no_frontend_coupling(self):
        text = WORKER_RUN_FILE.read_text(encoding="utf-8")
        forbidden = ["fastapi", "websocket", "starlette", "aiohttp"]
        hits = [tok for tok in forbidden if tok in text.lower()]
        assert not hits, (
            f"worker entrypoint must not import frontend / session code; found: {hits}"
        )


# ---- AC-6 ------------------------------------------------------------------


class TestAC6ProgressCorrectAfterReconnect:
    """AC-6: 浏览器重连后任务进度正确显示（从 DB 读取最新状态）。"""

    def test_task_api_reads_fresh_state_on_every_call(self, conn):
        """Simulate reconnect: browser A queries, disconnects; DB
        advances; browser B queries again and must see the new state."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from src.backend.api.routes.tasks import get_db, router
        from src.backend.db.repositories.async_task_repo import (
            AsyncTaskRepository,
        )

        repo = AsyncTaskRepository(conn)
        tid = repo.create(
            project_id="proj_a",
            phase=4,
            type="tts",
            params={},
        )
        repo.update_status(tid, "running")

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: conn
        app.include_router(router)
        client = TestClient(app)

        first = client.get("/api/projects/proj_a/tasks").json()
        first_row = {t["task_id"]: t for t in first["tasks"]}[tid]
        assert first_row["status"] == "running"
        assert first_row["progress"] == 0

        # Backend advances progress while the "browser" is disconnected.
        conn.execute(
            "UPDATE async_tasks SET progress = 75 WHERE task_id = ?",
            (tid,),
        )
        conn.commit()

        second = client.get("/api/projects/proj_a/tasks").json()
        second_row = {t["task_id"]: t for t in second["tasks"]}[tid]
        assert second_row["progress"] == 75, (
            f"reconnect must reflect DB-authoritative progress, "
            f"got {second_row['progress']}"
        )
        assert second_row["status"] == "running", (
            "status must also come straight from DB"
        )
