"""[SPEC-INTEG-007] WS /ws/{project_id} accept + heartbeat tests.

Only asserts:
  1. WS endpoint accepts connection (no 404)
  2. Server sends envelope-shaped greeting (ws.connected)
  3. Server responds to client ping with pong

Event broadcast (phase.advanced/status.changed etc.) deferred to Plan B (SPEC-11A).
"""
from __future__ import annotations

import json

from fastapi.testclient import TestClient

from src.backend.api.main import app


def test_ws_accepts_connection_and_sends_greeting() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws/proj_test_123") as ws:
        msg = ws.receive_text()
        envelope = json.loads(msg)
        assert envelope["type"] == "ws.connected"
        assert envelope["project_id"] == "proj_test_123"
        assert "timestamp" in envelope
        assert "payload" in envelope


def test_ws_responds_to_ping() -> None:
    client = TestClient(app)
    with client.websocket_connect("/ws/proj_ping") as ws:
        ws.receive_text()  # consume greeting
        ws.send_text(json.dumps({"type": "ping"}))
        msg = ws.receive_text()
        envelope = json.loads(msg)
        assert envelope["type"] == "pong"
        assert envelope["project_id"] == "proj_ping"
