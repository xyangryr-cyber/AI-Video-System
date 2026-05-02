"""[SPEC-INTEG-007|GAPFIX-018] WebSocket endpoint with ConnectionManager.

Provides:
- ConnectionManager — pools WebSocket connections grouped by project_id.
- Module-level manager singleton.
- /ws/{project_id} endpoint using ConnectionManager for accept/disconnect.
- ws.connected / ws.disconnected events broadcast on connect/disconnect.
- Client ping/pong heartbeat.

Envelope shape per SPEC-11A WsEventEnvelope.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

router = APIRouter()


class ConnectionManager:
    """Manages WebSocket connections grouped by project_id."""

    def __init__(self):
        self._connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, project_id: str) -> None:
        await websocket.accept()
        if project_id not in self._connections:
            self._connections[project_id] = set()
        self._connections[project_id].add(websocket)

    def disconnect(self, websocket: WebSocket, project_id: str) -> None:
        if project_id in self._connections:
            self._connections[project_id].discard(websocket)
            if not self._connections[project_id]:
                del self._connections[project_id]

    async def broadcast(self, project_id: str, event_type: str, payload: dict[str, Any]) -> None:
        """Broadcast to all connections for a specific project."""
        message = self._envelope(event_type, project_id, payload)
        dead: list[WebSocket] = []
        for ws in self._connections.get(project_id, set()):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, project_id)

    async def broadcast_all(self, event_type: str, payload: dict[str, Any]) -> None:
        """Broadcast to ALL connected clients (for system events)."""
        for project_id in list(self._connections.keys()):
            await self.broadcast(project_id, event_type, payload)

    @property
    def connection_count(self) -> int:
        return sum(len(v) for v in self._connections.values())

    @property
    def connections(self) -> dict[str, set[WebSocket]]:
        """Expose internal connections dict for test assertions."""
        return self._connections

    @staticmethod
    def _envelope(event_type: str, project_id: str, payload: dict[str, Any]) -> str:
        """Shape per SPEC-11A WsEventEnvelope."""
        return json.dumps({
            "type": event_type,
            "project_id": project_id,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
            "payload": payload,
        })


manager = ConnectionManager()


@router.websocket("/ws/{project_id}")
async def project_ws(websocket: WebSocket, project_id: str) -> None:
    await manager.connect(websocket, project_id)
    await manager.broadcast(project_id, "ws.connected", {})
    try:
        while True:
            raw = await websocket.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if msg.get("type") == "ping":
                await websocket.send_text(
                    ConnectionManager._envelope("pong", project_id, {})
                )
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket, project_id)
        await manager.broadcast(project_id, "ws.disconnected", {})
