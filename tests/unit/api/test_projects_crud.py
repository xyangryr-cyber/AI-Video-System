"""Tests for project CRUD endpoints that require DB writes."""

import sqlite3
import tempfile
from datetime import UTC
from pathlib import Path

from fastapi.testclient import TestClient

from src.backend.api.main import app
from src.backend.api.routes import projects
from src.backend.db.migration_runner import run_migrations


def _make_app_with_db() -> TestClient:
    """Create a TestClient with a fresh in-memory DB, migrations applied."""
    db_path = Path(tempfile.mkdtemp()) / "test.sqlite3"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    run_migrations(conn, Path("src/backend/db/migrations"))

    # Seed system_status so require_critical_ok passes
    from datetime import datetime, timedelta, timezone

    now = datetime.now(UTC)
    checked_at = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    valid_until = (now + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    for name in ("llm", "llm_review", "sqlite", "media_dir"):
        conn.execute(
            "INSERT INTO system_status(check_name, status, checked_at, valid_until) "
            "VALUES(?, 'ok', ?, ?)",
            (name, checked_at, valid_until),
        )
    conn.commit()

    app.dependency_overrides[projects.get_db] = lambda: conn
    client = TestClient(app)
    return client


def test_create_project_inserts_into_db():
    """POST /api/projects must INSERT into projects table and create 12 phase rows."""
    client = _make_app_with_db()

    resp = client.post(
        "/api/projects", json={"title": "Test Project", "description": "A description long enough"}
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["title"] == "Test Project"
    assert data["id"].startswith("proj_")

    # Verify DB state via GET /state
    state_resp = client.get(f"/api/projects/{data['id']}/state")
    assert state_resp.status_code == 200, state_resp.text
    state = state_resp.json()
    assert state["project"]["title"] == "Test Project"
    assert state["project"]["current_phase"] == 0
    assert len(state["phases"]) == 12


def test_create_project_then_list_shows_it():
    """After creating a project, it should appear in GET /api/projects."""
    client = _make_app_with_db()

    resp = client.post("/api/projects", json={"title": "List Test", "description": ""})
    assert resp.status_code == 201
    pid = resp.json()["id"]

    list_resp = client.get("/api/projects")
    assert list_resp.status_code == 200
    projects_list = list_resp.json()
    assert any(p["id"] == pid for p in projects_list)


def test_create_project_requires_title():
    """Empty title should be rejected by Pydantic validation."""
    client = _make_app_with_db()

    resp = client.post("/api/projects", json={"title": "", "description": ""})
    assert resp.status_code == 422


def test_get_project_returns_200():
    """GET /api/projects/{id} should return project detail."""
    client = _make_app_with_db()
    resp = client.post(
        "/api/projects", json={"title": "Detail Test", "description": "A description long enough"}
    )
    pid = resp.json()["id"]

    detail = client.get(f"/api/projects/{pid}")
    assert detail.status_code == 200
    data = detail.json()
    assert data["project_id"] == pid
    assert data["title"] == "Detail Test"


def test_get_project_404_for_missing():
    """GET /api/projects/{id} should return 404 for nonexistent project."""
    client = _make_app_with_db()
    resp = client.get("/api/projects/proj_nonexist")
    assert resp.status_code == 404


def test_delete_project_soft_deletes():
    """DELETE /api/projects/{id} soft-deletes (status='deleted')."""
    client = _make_app_with_db()
    resp = client.post("/api/projects", json={"title": "Delete Test", "description": ""})
    pid = resp.json()["id"]

    del_resp = client.delete(f"/api/projects/{pid}")
    assert del_resp.status_code == 200

    # Verify status changed to deleted
    detail = client.get(f"/api/projects/{pid}")
    assert detail.status_code == 200
    assert detail.json()["status"] == "deleted"


def test_delete_project_404_for_missing():
    """DELETE /api/projects/{id} should return 404 for nonexistent project."""
    client = _make_app_with_db()
    resp = client.delete("/api/projects/proj_nonexist")
    assert resp.status_code == 404
