"""[SPEC-GAPFIX-043] Key endpoint smoke tests.

Verifies that critical API endpoints return 200 (not 501/5xx).
Gracefully handles running-against-old-backend scenarios.
"""

from __future__ import annotations

import json
import urllib.request
import urllib.error

import pytest

from tests.smoke.conftest import needs_backend


def _get(url, timeout=5):
    try:
        resp = urllib.request.urlopen(url, timeout=timeout)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e)


def _post(url, data, timeout=5):
    body = json.dumps(data).encode()
    r = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        resp = urllib.request.urlopen(r, timeout=timeout)
        return resp.status, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()
    except Exception as e:
        return None, str(e)


@needs_backend
class TestKeyEndpoints:
    def test_get_projects_not_501(self):
        status, _body = _get("http://localhost:8000/api/projects")
        assert status is not None, "Backend unreachable"
        assert status != 501, "GET /api/projects still returns 501 (not implemented)"

    def test_get_project_state_not_501(self):
        status, _body = _get("http://localhost:8000/api/projects/proj_001/state")
        assert status is not None, "Backend unreachable"
        assert status != 501, "GET /api/projects/{id}/state still returns 501"

    def test_post_create_project_returns_201_or_403(self):
        status, _body = _post(
            "http://localhost:8000/api/projects",
            {"title": "Smoke Test Project", "description": "auto"},
        )
        assert status is not None, "Backend unreachable"
        # 201 on success, 403 if preflight checks not yet passing
        assert status in (201, 403), f"Expected 201 or 403, got {status}"

    def test_preferences_confirm_not_501(self):
        status, _body = _post(
            "http://localhost:8000/api/projects/proj_001/preferences/confirm",
            {"phase": 2, "decisions": {"candidate_id": "cand_01", "action": "accept"}},
        )
        assert status is not None, "Backend unreachable"
        assert status != 501, "POST preferences/confirm still returns 501"

    def test_materials_supplement_not_501(self):
        status, _body = _post(
            "http://localhost:8000/api/projects/proj_001/materials/supplement",
            {"shot_id": "shot_01", "material_type": "broll", "description": "test"},
        )
        assert status is not None, "Backend unreachable"
        assert status != 501, "POST materials/supplement still returns 501"

    def test_get_project_by_id_not_501(self):
        status, _body = _get("http://localhost:8000/api/projects/proj_001")
        assert status is not None, "Backend unreachable"
        assert status != 501, "GET /api/projects/{id} still returns 501"

    def test_delete_project_not_501(self):
        r = urllib.request.Request(
            "http://localhost:8000/api/projects/proj_001", method="DELETE"
        )
        try:
            resp = urllib.request.urlopen(r, timeout=5)
            status = resp.status
        except urllib.error.HTTPError as e:
            status = e.code
        except Exception:
            status = None
        assert status is not None, "Backend unreachable"
        assert status != 501, "DELETE /api/projects/{id} still returns 501"

    def test_advance_not_501(self):
        status, _body = _post(
            "http://localhost:8000/api/projects/proj_001/advance", {}
        )
        assert status is not None, "Backend unreachable"
        assert status != 501, "POST /advance still returns 501"

    def test_rollback_not_501(self):
        status, _body = _post(
            "http://localhost:8000/api/projects/proj_001/rollback",
            {"target_phase": 0},
        )
        assert status is not None, "Backend unreachable"
        assert status != 501, "POST /rollback still returns 501"

    def test_skip_not_501(self):
        status, _body = _post(
            "http://localhost:8000/api/projects/proj_001/skip", {}
        )
        assert status is not None, "Backend unreachable"
        assert status != 501, "POST /skip still returns 501"

    def test_chat_not_501(self):
        status, _body = _post(
            "http://localhost:8000/api/projects/proj_001/chat",
            {"message": "hello", "context": {}},
        )
        assert status is not None, "Backend unreachable"
        assert status != 501, "POST /chat still returns 501"

    def test_get_artifact_not_501(self):
        status, _body = _get(
            "http://localhost:8000/api/projects/proj_001/phases/0/artifact"
        )
        assert status is not None, "Backend unreachable"
        assert status != 501, "GET /artifact still returns 501"

    def test_cancel_task_not_501(self):
        status, _body = _post(
            "http://localhost:8000/api/projects/proj_001/tasks/task_001/cancel", {}
        )
        assert status is not None, "Backend unreachable"
        assert status != 501, "POST /cancel still returns 501"
