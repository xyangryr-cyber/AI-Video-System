"""Huey (SqliteHuey) task-queue configuration.

SPEC-B-003 pins the queue parameters:

* heartbeat every 5s, scan every 30s
* default_max_attempts = 3
* stale_threshold = task_timeout + 60s
* per-task timeouts: tts=600s, keyframe=1800s, rough=1800s, final=2400s
* SqliteHuey backend with the DB file in ``data/db/``

``huey`` itself is imported lazily by :func:`build_huey` so unit tests
can verify the constants without installing the package.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

HEARTBEAT_SEC: int = 5
SCAN_INTERVAL_SEC: int = 30
DEFAULT_MAX_ATTEMPTS: int = 3
STALE_THRESHOLD_GRACE_SEC: int = 60

TASK_TIMEOUTS: dict[str, int] = {
    "tts": 600,
    "bgm": 600,
    "sfx": 600,
    "keyframe": 1800,
    "rough": 1800,
    "final": 2400,
}

DEFAULT_DB_DIR: Path = Path("data/db")
DEFAULT_HUEY_DB_FILE: str = "huey_queue.sqlite3"
HUEY_NAME: str = "ai_video_system"


def stale_threshold_for(task_type: str) -> int:
    """Return ``task_timeout + STALE_THRESHOLD_GRACE_SEC``.

    Raises ``KeyError`` for unknown task types so callers fail loudly
    instead of silently defaulting.
    """
    return TASK_TIMEOUTS[task_type] + STALE_THRESHOLD_GRACE_SEC


def build_huey(db_dir: Path | None = None, immediate: bool = False) -> Any:
    """Instantiate ``SqliteHuey`` with the SPEC-B-003 parameters.

    Imports :mod:`huey` lazily; unit tests exercising the constants
    above do not need the package installed.

    When *immediate* is ``True`` the returned huey instance executes
    tasks synchronously in-process (used by BDD :memory: fixtures).
    """
    from huey import SqliteHuey  # type: ignore[import-untyped]

    directory = Path(db_dir) if db_dir is not None else DEFAULT_DB_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return SqliteHuey(
        name=HUEY_NAME,
        filename=str(directory / DEFAULT_HUEY_DB_FILE),
        immediate=immediate,
    )


def huey_enqueue_runner(
    huey: Any,
    task_registry: dict[str, Callable],
) -> Callable[[str, str, dict], None]:
    """Return a ``task_runner`` callable compatible with G-000a.

    The returned runner looks up *task_type* in *task_registry* and
    calls the corresponding huey task function with ``(task_id, params)``.
    """

    def run(task_type: str, task_id: str, params: dict) -> None:
        task_fn = task_registry[task_type]
        task_fn(task_id, params)

    return run
