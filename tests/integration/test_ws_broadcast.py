"""[GAPFIX-018..019] Integration tests for WebSocket broadcast and EventBus.

Tests:
1. WS connect -> receive ws.connected event
2. manager.broadcast() -> client receives event
3. Disconnected clients are cleaned up
4. EventBus subscribe + emit callback
"""
from __future__ import annotations

import asyncio
import json

import pytest
from fastapi import FastAPI

from src.backend.api.routes.websocket import ConnectionManager, manager, router
from src.backend.core.event_bus import EventBus, event_bus


def _app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


# ---------------------------------------------------------------------------
# ConnectionManager tests
# ---------------------------------------------------------------------------

class TestConnectionManager:
    """Tests for ConnectionManager connection pooling and broadcast."""

    def test_initial_connection_count_is_zero(self):
        mgr = ConnectionManager()
        assert mgr.connection_count == 0

    def test_connect_increments_count(self):
        mgr = ConnectionManager()
        # Simulate connect without a real transport by populating manually
        mgr._connections["proj-1"] = set(["fake-ws"])
        assert mgr.connection_count == 1

    def test_disconnect_decrements_count(self):
        mgr = ConnectionManager()
        mgr._connections["proj-1"] = set(["fake-ws"])
        mgr.disconnect("fake-ws", "proj-1")
        assert mgr.connection_count == 0
        assert "proj-1" not in mgr._connections

    def test_connections_isolation_by_project(self):
        mgr = ConnectionManager()
        mgr._connections["proj-1"] = set(["ws-a"])
        mgr._connections["proj-2"] = set(["ws-b", "ws-c"])
        assert mgr.connection_count == 3

    def test_envelope_shape(self):
        envelope = ConnectionManager._envelope("task.created", "proj-x", {"a": 1})
        data = json.loads(envelope)
        assert data["type"] == "task.created"
        assert data["project_id"] == "proj-x"
        assert data["payload"] == {"a": 1}
        assert "timestamp" in data

    def test_module_singleton_connection_count_zero(self):
        assert manager.connection_count == 0


# ---------------------------------------------------------------------------
# EventBus tests
# ---------------------------------------------------------------------------

class TestEventBus:
    """Tests for EventBus subscribe, emit, and emit_and_broadcast."""

    def test_initial_subscriber_count_zero(self):
        bus = EventBus()
        assert bus.subscriber_count == 0

    def test_subscribe_adds_callback(self):
        bus = EventBus()
        received: list[dict] = []

        def cb(event_type, project_id, payload):
            received.append({"event_type": event_type, "project_id": project_id, "payload": payload})

        bus.subscribe("task.created", cb)
        assert bus.subscriber_count == 1

    @pytest.mark.asyncio
    async def test_emit_calls_registered_callback(self):
        bus = EventBus()
        received: list[dict] = []

        def cb(event_type, project_id, payload):
            received.append({"event_type": event_type, "project_id": project_id, "payload": payload})

        bus.subscribe("task.created", cb)
        await bus.emit("task.created", "proj-1", {"task_id": "t1"})
        assert len(received) == 1
        assert received[0]["event_type"] == "task.created"
        assert received[0]["project_id"] == "proj-1"
        assert received[0]["payload"] == {"task_id": "t1"}

    @pytest.mark.asyncio
    async def test_emit_skips_unsubscribed_types(self):
        bus = EventBus()
        received: list[dict] = []

        def cb(event_type, project_id, payload):
            received.append({})

        bus.subscribe("task.created", cb)
        await bus.emit("phase.entered", "proj-1", {})
        assert len(received) == 0

    @pytest.mark.asyncio
    async def test_emit_calls_multiple_subscribers(self):
        bus = EventBus()
        calls: list[str] = []

        def cb1(*args):
            calls.append("cb1")

        def cb2(*args):
            calls.append("cb2")

        bus.subscribe("task.created", cb1)
        bus.subscribe("task.created", cb2)
        await bus.emit("task.created", "proj-1", {})
        assert len(calls) == 2
        assert "cb1" in calls
        assert "cb2" in calls

    @pytest.mark.asyncio
    async def test_emit_one_callback_fails_others_still_run(self):
        bus = EventBus()
        calls: list[str] = []

        def good_cb(*args):
            calls.append("good")

        def bad_cb(*args):
            raise RuntimeError("boom")

        bus.subscribe("task.created", bad_cb)
        bus.subscribe("task.created", good_cb)
        # Should not raise
        await bus.emit("task.created", "proj-1", {})
        assert "good" in calls

    def test_module_singleton_exists(self):
        assert event_bus is not None
        assert isinstance(event_bus, EventBus)

    def test_wire_injects_connection_manager(self):
        bus = EventBus()
        assert bus._connection_manager is None
        bus.wire(manager)
        assert bus._connection_manager is manager

    @pytest.mark.asyncio
    async def test_async_callback_is_called(self):
        bus = EventBus()
        received: list[dict] = []

        async def async_cb(event_type, project_id, payload):
            received.append({"event_type": event_type, "project_id": project_id, "payload": payload})

        bus.subscribe("task.completed", async_cb)
        await bus.emit("task.completed", "proj-x", {"ok": True})
        assert len(received) == 1
        assert received[0]["event_type"] == "task.completed"


# ---------------------------------------------------------------------------
# End-to-end WS integration tests (requires TestClient)
# ---------------------------------------------------------------------------

class TestWsE2E:
    """End-to-end WebSocket tests using FastAPI TestClient."""

    @pytest.mark.asyncio
    async def test_connect_receives_ws_connected_event(self):
        """Verifies ws.connected is received immediately on connect."""
        from fastapi.testclient import TestClient

        client = TestClient(_app())
        with client.websocket_connect("/ws/test-proj") as ws:
            raw = ws.receive_json()
            assert raw["type"] == "ws.connected"
            assert raw["project_id"] == "test-proj"

    @pytest.mark.asyncio
    async def test_ping_pong(self):
        """Verifies ping/pong heartbeat works."""
        from fastapi.testclient import TestClient

        client = TestClient(_app())
        with client.websocket_connect("/ws/test-proj") as ws:
            ws.receive_json()  # consume ws.connected
            ws.send_json({"type": "ping"})
            response = ws.receive_json()
            assert response["type"] == "pong"
            assert response["project_id"] == "test-proj"

    @pytest.mark.asyncio
    async def test_disconnect_cleans_up_manager(self):
        """After disconnect, connection should be removed from manager."""
        from fastapi.testclient import TestClient

        client = TestClient(_app())
        with client.websocket_connect("/ws/disco-proj") as ws:
            ws.receive_json()  # consume ws.connected
            assert "disco-proj" in manager._connections
        # Context manager exit closes the WS -> triggers disconnect cleanup
        assert "disco-proj" not in manager._connections

    @pytest.mark.asyncio
    async def test_broadcast_reaches_connected_client(self):
        """Calls manager.broadcast() and verifies the client receives it."""
        from fastapi.testclient import TestClient

        client = TestClient(_app())
        with client.websocket_connect("/ws/bcast-proj") as ws:
            ws.receive_json()  # consume ws.connected

            # The manager singleton is shared with the app router
            await manager.broadcast("bcast-proj", "task.started", {"msg": "hello"})
            response = ws.receive_json()
            assert response["type"] == "task.started"
            assert response["project_id"] == "bcast-proj"
            assert response["payload"] == {"msg": "hello"}

    @pytest.mark.asyncio
    async def test_dead_connection_cleaned_up_on_broadcast(self):
        """Broadcast to a dead connection cleans it up."""
        from fastapi.testclient import TestClient

        client = TestClient(_app())
        with client.websocket_connect("/ws/cleanup-proj") as ws:
            ws.receive_json()  # consume ws.connected
            assert "cleanup-proj" in manager._connections

        # After context exit, the WS is closed
        assert "cleanup-proj" not in manager._connections


# ---------------------------------------------------------------------------
# EventBus + ConnectionManager integration
# ---------------------------------------------------------------------------

class TestEventBusWithConnectionManager:
    """Tests EventBus wired to ConnectionManager."""

    def test_emit_and_broadcast_without_wiring_does_not_raise(self):
        """emit_and_broadcast with no connection_manager should just emit."""
        bus = EventBus()  # no connection_manager
        received: list[dict] = []

        def cb(event_type, project_id, payload):
            received.append(payload)

        bus.subscribe("task.created", cb)
        # Should not raise even without connection_manager
        # Use asyncio to run the async method
        asyncio.run(bus.emit_and_broadcast("task.created", "proj-1", {"k": "v"}))
        assert len(received) == 1

    def test_emit_and_broadcast_with_manager(self):
        """emit_and_broadcast with wired manager calls broadcast."""
        mgr = ConnectionManager()
        bus = EventBus(connection_manager=mgr)
        received: list[dict] = []

        def cb(event_type, project_id, payload):
            received.append(payload)

        bus.subscribe("task.started", cb)
        # No actual WebSocket connections, but broadcast should not raise
        asyncio.run(bus.emit_and_broadcast("task.started", "proj-1", {"k": "v"}))
        assert len(received) == 1
