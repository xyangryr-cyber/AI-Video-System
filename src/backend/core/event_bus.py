"""[GAPFIX-019] EventBus for internal event dispatch + optional WS broadcast.

The EventBus maintains a registry of async callbacks keyed by event type
string.  Callbacks are async functions with the signature:

    async def callback(event_type: str, project_id: str, payload: dict) -> None

A module-level singleton ``event_bus`` is created without a
ConnectionManager.  The ConnectionManager is wired in at app startup
(main.py) so that emit_and_broadcast() can push events to WebSocket
clients.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

EventCallback = Callable[..., object]


class EventBus:
    """In-process async event bus with optional WebSocket broadcast."""

    def __init__(self, connection_manager: Any | None = None):
        self._subscribers: dict[str, list[EventCallback]] = {}
        self._connection_manager = connection_manager

    def subscribe(self, event_type: str, callback: EventCallback) -> None:
        """Register a callback for a specific event type.

        The callback signature must be:
            async def callback(event_type: str, project_id: str, payload: dict) -> None
            (or a sync def — both are supported via ``await`` attempt).
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

    async def emit(self, event_type: str, project_id: str, payload: dict) -> None:
        """Call all registered callbacks for the event type.

        Callbacks are tried best-effort: a single failing callback does
        NOT prevent other callbacks from running.
        """
        import asyncio

        for cb in self._subscribers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(cb):
                    await cb(event_type, project_id, payload)
                else:
                    cb(event_type, project_id, payload)
            except Exception:
                pass

    async def emit_and_broadcast(self, event_type: str, project_id: str, payload: dict) -> None:
        """Emit to callbacks AND broadcast via ConnectionManager."""
        await self.emit(event_type, project_id, payload)
        if self._connection_manager is not None:
            await self._connection_manager.broadcast(project_id, event_type, payload)

    def wire(self, connection_manager: Any) -> None:
        """Inject the ConnectionManager dependency (called at startup)."""
        self._connection_manager = connection_manager

    @property
    def subscriber_count(self) -> int:
        """Total number of registered callback subscriptions."""
        return sum(len(v) for v in self._subscribers.values())


event_bus = EventBus()
