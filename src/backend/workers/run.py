"""Worker entrypoint (docker-compose ``worker`` service).

Runs the Huey consumer against the SqliteHuey backend configured in
:mod:`src.backend.workers.huey_config`. Equivalent to invoking
``huey_consumer`` directly but keeps startup in one import path so
tasks and shared constants load before the consumer picks up work.

On startup (SPEC-B-005) we also sweep ``async_tasks`` for orphan rows
left behind by a previous crash -- rows still marked ``running`` but
whose worker is gone. Orphans are re-queued (attempts remaining) or
marked ``failed`` (attempts exhausted). This makes a restart self-
healing after ``kill -9`` or container OOM.
"""

from __future__ import annotations

import datetime as _dt
import sqlite3

from src.backend.workers import tasks as _tasks  # noqa: F401  -- register tasks
from src.backend.workers.huey_config import (
    DEFAULT_MAX_ATTEMPTS,
    HEARTBEAT_SEC,
    SCAN_INTERVAL_SEC,
    STALE_THRESHOLD_GRACE_SEC,
    TASK_TIMEOUTS,
    build_huey,
)
from src.backend.workers.recovery import recover_orphans

_APP_DB_PATH = "data/db/app.sqlite3"


def _startup_stale_cutoff() -> str:
    """Cutoff = now - max(task_timeout) - grace.

    Any ``started_at`` older than this is unambiguously orphaned: even
    the longest legitimate task would have updated its heartbeat by now.
    """
    horizon_sec = max(TASK_TIMEOUTS.values()) + STALE_THRESHOLD_GRACE_SEC
    cutoff = _dt.datetime.now(_dt.UTC) - _dt.timedelta(seconds=horizon_sec)
    return cutoff.strftime("%Y-%m-%dT%H:%M:%S.") + f"{cutoff.microsecond // 1000:03d}Z"


def sweep_orphans_on_startup(db_path: str = _APP_DB_PATH) -> None:
    """Best-effort orphan recovery at worker boot. Silently skips if
    the app DB is absent (fresh install / test environment)."""
    try:
        conn = sqlite3.connect(db_path)
    except sqlite3.OperationalError:
        return
    try:
        conn.row_factory = sqlite3.Row
        recover_orphans(conn, stale_before=_startup_stale_cutoff())
    finally:
        conn.close()


def main() -> None:
    from huey.consumer import Consumer

    sweep_orphans_on_startup()

    huey = build_huey()
    consumer = Consumer(
        huey,
        workers=1,
        worker_type="thread",
        health_check_interval=HEARTBEAT_SEC,
        scheduler_interval=SCAN_INTERVAL_SEC,
        max_delay=10.0,
        initial_delay=0.1,
        check_worker_health=True,
        flush_locks=False,
    )
    assert DEFAULT_MAX_ATTEMPTS == 3
    consumer.run()


if __name__ == "__main__":
    main()
