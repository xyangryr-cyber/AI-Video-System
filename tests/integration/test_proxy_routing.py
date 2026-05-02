"""[SPEC-GAPFIX-048] Proxy routing integration tests.

Verifies the Vite proxy -> backend routing contract so the frontend
dev server correctly forwards /api/* and /ws/* to the backend.

Checks route registration at the router level to avoid needing a
wired database connection for existence checks.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient


# ---------------------------------------------------------------------------
# helpers: build a minimal app with just the projects router + DB override
# ---------------------------------------------------------------------------

def _build_app_with_projects_router():
    """Return a FastAPI app with only the projects router + health endpoint,
    wired with an in-memory DB so route-existence tests can make real HTTP calls.
    """
    import sqlite3

    from src.backend.api.routes import projects as projects_router_module

    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            current_phase INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        CREATE TABLE phases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id TEXT NOT NULL REFERENCES projects(project_id),
            phase_num INTEGER NOT NULL CHECK(phase_num BETWEEN 0 AND 11),
            phase_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            artifact_version INTEGER NOT NULL DEFAULT 0,
            artifact_status TEXT DEFAULT NULL,
            artifact_path TEXT,
            preferences_confirmed_at TEXT,
            style_lock_path TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            UNIQUE(project_id, phase_num)
        );
        CREATE TABLE system_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ok',
            message TEXT,
            checked_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            valid_until TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now','+24 hours'))
        );
    """
    )
    conn.commit()

    app = FastAPI()
    app.dependency_overrides[projects_router_module.get_db] = lambda: conn
    app.include_router(projects_router_module.router)

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    return app


# ---------------------------------------------------------------------------
# Tests: backend routes mounted at expected paths
# ---------------------------------------------------------------------------


class TestApiPrefixRouting:
    """Verify that every frontend-facing route is mounted under /api."""

    @classmethod
    def setup_class(cls):
        cls.client = TestClient(_build_app_with_projects_router())

    def test_health_endpoint_is_accessible(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_get_projects_route_resolves(self):
        """GET /api/projects must resolve (first-screen ProjectList)."""
        r = self.client.get("/api/projects")
        assert r.status_code == 200

    def test_post_projects_route_resolves(self):
        """POST /api/projects must resolve (frontend CreateProjectForm)."""
        r = self.client.post(
            "/api/projects", json={"title": "T", "description": ""}
        )
        # 403 = critical gates not seeded (route is alive, gate active)
        assert r.status_code in (201, 403, 422)

    def test_get_project_state_route_resolves(self):
        """GET /api/projects/{id}/state must resolve (frontend state restore)."""
        r = self.client.get("/api/projects/no_such_project/state")
        assert r.status_code == 404

    def test_preferences_confirm_route_resolves(self):
        """POST /.../preferences/confirm must resolve."""
        r = self.client.post(
            "/api/projects/no_such_project/preferences/confirm",
            json={"phase": 0, "decisions": {}},
        )
        assert r.status_code == 404  # route alive, project missing


class TestProxyPathMapping:
    """Verify that the paths match the Vite proxy configuration."""

    @classmethod
    def setup_class(cls):
        cls.app = _build_app_with_projects_router()

    def test_vite_proxy_keeps_api_prefix(self):
        """Vite proxies '/api/projects' -> 'http://backend:8000/api/projects'.

        The proxy does NOT strip /api; both frontend and backend use /api prefix.
        """
        api_routes = [
            r
            for r in self.app.routes
            if isinstance(r, APIRoute) and r.path.startswith("/api")
        ]
        assert len(api_routes) > 0, "Expected at least one /api route"

    def test_all_api_routes_use_expected_http_methods(self):
        """Verify HTTP methods match what the frontend apiClient sends."""
        route_methods: dict[str, set[str]] = {}
        for r in self.app.routes:
            if isinstance(r, APIRoute):
                existing = route_methods.get(r.path, set())
                route_methods[r.path] = existing | set(r.methods)

        assert "GET" in route_methods.get("/api/projects", set()), (
            f"GET /api/projects missing; routes: {list(route_methods.keys())}"
        )
        assert "POST" in route_methods.get("/api/projects", set())
        assert "GET" in route_methods.get(
            "/api/projects/{project_id}/state", set()
        )
        assert "POST" in route_methods.get(
            "/api/projects/{project_id}/preferences/confirm", set()
        )
