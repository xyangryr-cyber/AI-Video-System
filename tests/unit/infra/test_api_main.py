"""Test FastAPI app entrypoint exists and exports /health."""

from __future__ import annotations


class TestAppEntrypoint:
    def test_app_importable(self):
        from src.backend.api.main import app

        assert app is not None
        assert app.title is not None

    def test_health_endpoint_registered(self):
        from src.backend.api.main import app

        routes = [r.path for r in app.routes]
        assert "/health" in routes

    def test_health_returns_ok(self):
        from fastapi.testclient import TestClient
        from src.backend.api.main import app

        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
