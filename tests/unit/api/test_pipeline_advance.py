"""Tests for advance/rollback/skip pipeline endpoints."""

import sqlite3
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from src.backend.api.main import app
from src.backend.db.migration_runner import run_migrations
from src.backend.api.routes import projects


def _make_app_with_project() -> tuple[TestClient, str]:
    """Create TestClient with seeded DB and one project at phase 0."""
    db_path = Path(tempfile.mkdtemp()) / "test.sqlite3"
    conn = sqlite3.connect(str(db_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    run_migrations(conn, Path("src/backend/db/migrations"))

    from datetime import datetime, timedelta, timezone
    now = datetime.now(timezone.utc)
    checked_at = now.strftime("%Y-%m-%dT%H:%M:%S.000Z")
    valid_until = (now + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    for name in ("llm", "llm_review", "sqlite", "media_dir"):
        conn.execute(
            "INSERT INTO system_status(check_name, status, checked_at, valid_until) "
            "VALUES(?, 'ok', ?, ?)", (name, checked_at, valid_until),
        )
    conn.commit()

    app.dependency_overrides[projects.get_db] = lambda: conn
    client = TestClient(app)

    resp = client.post("/api/projects", json={"title": "Advance Test", "description": ""})
    assert resp.status_code == 201
    return client, resp.json()["id"]


def test_advance_not_501():
    """POST /advance should not return 501."""
    client, pid = _make_app_with_project()
    resp = client.post(f"/api/projects/{pid}/advance")
    assert resp.status_code != 501, f"Still 501: {resp.json()}"


def test_advance_404_for_missing_project():
    """POST /advance on nonexistent project returns 404."""
    client, _ = _make_app_with_project()
    resp = client.post("/api/projects/proj_nonexist/advance")
    assert resp.status_code == 404


def test_rollback_not_501():
    """POST /rollback should not return 501."""
    client, pid = _make_app_with_project()
    resp = client.post(f"/api/projects/{pid}/rollback", json={"target_phase": 0})
    assert resp.status_code != 501, f"Still 501: {resp.json()}"


def test_rollback_404_for_missing_project():
    """POST /rollback on nonexistent project returns 404."""
    client, _ = _make_app_with_project()
    resp = client.post("/api/projects/proj_nonexist/rollback", json={"target_phase": 0})
    assert resp.status_code == 404


def test_skip_not_501():
    """POST /skip should not return 501."""
    client, pid = _make_app_with_project()
    resp = client.post(f"/api/projects/{pid}/skip")
    assert resp.status_code != 501, f"Still 501: {resp.json()}"
