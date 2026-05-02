"""Single-tab lock per project (SPEC-B-012 AC-1).

Prevents concurrent editing of the same project from multiple browser tabs.
Second connection receives 409 Conflict with a human-readable message.
"""

from __future__ import annotations

import threading
import time


class SingleTabLock:
    """In-memory lock: one active session per project_id.

    V1 single-process deployment; multi-process would need Redis / DB lock.
    """

    def __init__(self) -> None:
        self._locks: dict[str, str] = {}
        self._lock = threading.Lock()

    def try_acquire(self, project_id: str) -> tuple[bool, str]:
        """Return (allowed, message). First caller gets the lock; second
        gets 409 Conflict.
        """
        with self._lock:
            if project_id in self._locks:
                return False, (
                    f"409 Conflict: project {project_id} is already open in "
                    f"another tab. Close that tab before opening a new one."
                )
            self._locks[project_id] = str(time.time())
            return True, ""

    def release(self, project_id: str) -> None:
        with self._lock:
            self._locks.pop(project_id, None)
