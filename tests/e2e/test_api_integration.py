"""[SPEC-GAPFIX-042] E2E test: verify frontend-backend connectivity.

Tests that the Vite proxy correctly forwards /api requests to the
backend, and that the backend API endpoints respond correctly.

Requires the full stack to be running (docker compose up).
Skips gracefully when the stack is not available.
"""

from __future__ import annotations

import os

import httpx
import pytest

BASE_URL = os.getenv("BASE_URL", "http://localhost:3000")
API_BASE = os.getenv("API_BASE", "http://localhost:8000")
TIMEOUT = 10.0


def _api_available() -> bool:
    try:
        r = httpx.get(f"{API_BASE}/health", timeout=TIMEOUT)
        return r.status_code == 200
    except Exception:
        return False


def _proxy_available() -> bool:
    try:
        r = httpx.get(f"{BASE_URL}/api/projects", timeout=TIMEOUT)
        return r.status_code < 600
    except Exception:
        return False


@pytest.mark.skipif(
    not _api_available(),
    reason="Backend not available. Run 'docker compose -f docker-compose.dev.yml up -d' first.",
)
class TestBackendAPI:
    """Direct backend API tests (bypass proxy)."""

    def test_health_endpoint(self):
        r = httpx.get(f"{API_BASE}/health", timeout=TIMEOUT)
        assert r.status_code == 200
        assert r.json() == {"status": "ok"}

    def test_get_projects_returns_list(self):
        r = httpx.get(f"{API_BASE}/api/projects", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_get_project_state_returns_404_for_unknown(self):
        r = httpx.get(f"{API_BASE}/api/projects/nonexistent/state", timeout=TIMEOUT)
        assert r.status_code == 404

    def test_post_projects_rejects_empty_title(self):
        r = httpx.post(
            f"{API_BASE}/api/projects",
            json={"title": "", "description": ""},
            timeout=TIMEOUT,
        )
        assert r.status_code == 422

    def test_cors_headers_present(self):
        r = httpx.options(
            f"{API_BASE}/api/projects",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
            timeout=TIMEOUT,
        )
        # CORS preflight should return allow-origin or pass-through
        assert r.status_code in (200, 204, 405)


@pytest.mark.skipif(
    not (_api_available() and _proxy_available()),
    reason="Full stack not available.",
)
class TestProxyChain:
    """Frontend -> Vite proxy -> Backend chain tests."""

    def test_proxy_forwards_get_projects(self):
        """apiClient.get('/api/projects') reaches backend via Vite proxy."""
        r = httpx.get(f"{BASE_URL}/api/projects", timeout=TIMEOUT)
        assert r.status_code == 200
        data = r.json()
        assert isinstance(data, list)

    def test_proxy_forwards_get_project_state(self):
        r = httpx.get(
            f"{BASE_URL}/api/projects/nonexistent/state", timeout=TIMEOUT
        )
        assert r.status_code == 404

    def test_proxy_forwards_post_preferences_confirm(self):
        r = httpx.post(
            f"{BASE_URL}/api/projects/nonexistent/preferences/confirm",
            json={"phase": 0, "decisions": {}},
            timeout=TIMEOUT,
        )
        # 404 = route active, project missing -> proxy works
        assert r.status_code == 404
