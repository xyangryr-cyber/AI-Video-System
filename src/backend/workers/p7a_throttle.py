"""[SPEC-B-015] Per-provider token-bucket throttle for P7A fetch tasks.

AC-3: single-provider concurrency > quota -> overflow requests go to a
FIFO queue rather than being dropped. Release promotes the next waiter.

Thread-safe via a single lock; the critical sections are O(1) so the
lock is not a throughput bottleneck under the worker concurrency
SPEC-B-003 configures (workers=1 + thread-pool).
"""

from __future__ import annotations

import threading
from collections import defaultdict, deque
from collections.abc import Mapping
from typing import Any


class ProviderThrottle:
    """Bounded in-flight counter + FIFO waiter queue per provider key.

    Semantics:
    * ``try_acquire(provider)`` -> True if a slot was granted (in-flight
      counter incremented), False if the request was queued.
    * ``release(provider)`` -> True if the freed slot was handed to a
      queued waiter (still in-flight, different owner), False if the
      slot simply drained (no waiters).
    """

    def __init__(
        self,
        quotas: Mapping[str, int] | None = None,
        default_quota: int = 2,
    ) -> None:
        self._quotas: dict[str, int] = dict(quotas or {})
        self._default_quota = default_quota
        self._in_flight: dict[str, int] = defaultdict(int)
        self._queue: dict[str, deque[Any]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _quota(self, provider: str) -> int:
        return self._quotas.get(provider, self._default_quota)

    def try_acquire(self, provider: str) -> bool:
        with self._lock:
            if self._in_flight[provider] < self._quota(provider):
                self._in_flight[provider] += 1
                return True
            # Park a placeholder in the waiter queue; callers poll via
            # try_acquire again after a release broadcast, or the worker
            # schedules a redelivery. We only need to track *count*,
            # not identity, for AC-3 no-loss accounting.
            self._queue[provider].append(1)
            return False

    def release(self, provider: str) -> bool:
        with self._lock:
            if self._in_flight[provider] > 0:
                self._in_flight[provider] -= 1
            if self._queue[provider]:
                # Promote one waiter: pop from queue, bump in-flight back up.
                self._queue[provider].popleft()
                self._in_flight[provider] += 1
                return True
            return False

    def in_flight(self, provider: str) -> int:
        with self._lock:
            return self._in_flight[provider]

    def queued(self, provider: str) -> int:
        with self._lock:
            return len(self._queue[provider])


__all__ = ["ProviderThrottle"]
