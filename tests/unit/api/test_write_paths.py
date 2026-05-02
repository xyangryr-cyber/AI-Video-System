"""Tests for confirm_preferences and material_supplement write paths."""

import json as _json
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
    resp = client.post("/api/projects", json={"title": "Write Test", "description": ""})
    return client, resp.json()["id"]


def test_confirm_preferences_writes_to_db():
    """POST /preferences/confirm should write to preferences table."""
    client, pid = _make_client_and_project()
    conn = app.dependency_overrides[projects.get_db]()

    resp = client.post(f"/api/projects/{pid}/preferences/confirm", json={
        "phase": 2, "decisions": {"candidate_id": "cand_01", "action": "accept"}
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True

    # DB should have preferences row
    prefs_row = conn.execute(
        "SELECT project_id, last_candidates_json, last_confirmed_at "
        "FROM preferences WHERE project_id = ?",
        (pid,),
    ).fetchone()
    assert prefs_row is not None, "preferences row not written"
    assert prefs_row["last_confirmed_at"] is not None

    # Phase should be marked confirmed
    phase_row = conn.execute(
        "SELECT preferences_confirmed_at FROM phases "
        "WHERE project_id = ? AND phase_num = 2",
        (pid,),
    ).fetchone()
    assert phase_row is not None
    assert phase_row["preferences_confirmed_at"] is not None


def test_material_supplement_creates_async_task():
    """POST /materials/supplement should create async_task record."""
    client, pid = _make_client_and_project()
    conn = app.dependency_overrides[projects.get_db]()

    resp = client.post(f"/api/projects/{pid}/materials/supplement", json={
        "shot_id": "shot_01", "material_type": "broll", "description": "crowd"
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["task_id"].startswith("task_")

    task_row = conn.execute(
        "SELECT task_id, project_id, type, status FROM async_tasks WHERE task_id = ?",
        (data["task_id"],),
    ).fetchone()
    assert task_row is not None, "async_task not created"
    assert task_row["project_id"] == pid
    assert task_row["status"] == "pending"
