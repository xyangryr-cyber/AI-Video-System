"""Tests for artifact and cancel endpoints."""

import sqlite3
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from src.backend.api.main import app
from src.backend.db.migration_runner import run_migrations
from src.backend.api.routes import projects


def _make_client_and_project() -> tuple[TestClient, str]:
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
    resp = client.post("/api/projects", json={"title": "Aux Test", "description": ""})
    return client, resp.json()["id"]


def test_get_artifact_not_501():
    """GET /phases/{p}/artifact should not return 501."""
    client, pid = _make_client_and_project()
    resp = client.get(f"/api/projects/{pid}/phases/0/artifact")
    assert resp.status_code != 501, f"Still 501: {resp.json()}"


def test_get_artifact_404_for_missing_project():
    """GET /artifact on nonexistent project returns 404."""
    client, _ = _make_client_and_project()
    resp = client.get("/api/projects/proj_nonexist/phases/0/artifact")
    assert resp.status_code == 404


def test_cancel_task_not_501():
    """POST /tasks/{task_id}/cancel should not return 501."""
    client, pid = _make_client_and_project()
    resp = client.post(f"/api/projects/{pid}/tasks/task_001/cancel")
    assert resp.status_code != 501, f"Still 501: {resp.json()}"
