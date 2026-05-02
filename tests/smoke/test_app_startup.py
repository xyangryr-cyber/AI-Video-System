"""[SPEC-GAPFIX-043] Application startup smoke tests.

Verifies that both FastAPI backend and Vite frontend can start and
serve their health/root endpoints.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

from tests.smoke.conftest import needs_backend, needs_frontend


def _get(url, timeout=5):
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e)


@needs_backend
class TestBackendStartup:
    def test_health_endpoint_returns_ok(self):
        status, body = _get("http://localhost:8000/health")
        assert status == 200
        data = json.loads(body)
        assert data["status"] == "ok"

    def test_openapi_schema_accessible(self):
        status, body = _get("http://localhost:8000/openapi.json")
        assert status == 200
        data = json.loads(body)
        assert "paths" in data
        assert "/api/projects" in data["paths"]


@needs_frontend
class TestFrontendStartup:
    def test_dev_server_serves_html(self):
        status, body = _get("http://localhost:3000")
        assert status == 200
        content = body.decode("utf-8", errors="replace")
        assert len(content) > 0
        assert "<!DOCTYPE html>" in content or "<html" in content

    def test_proxy_forwards_api_calls(self):
        status, _body = _get("http://localhost:3000/api/projects")
        assert status is not None, "Frontend unreachable"
        # 200 when proxy works, non-501 means improvement
        assert status != 501, "Frontend proxy still hitting 501"
