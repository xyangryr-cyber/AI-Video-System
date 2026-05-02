"""[SPEC-GAPFIX-048] HTTP integration tests for frontend apiClient -> backend API.

Verifies the complete HTTP request/response chain for the three
endpoints that the frontend depends on for first-screen render:
  - GET  /api/projects
  - POST /api/projects
  - GET  /api/projects/{id}/state

Uses FastAPI TestClient with an in-memory SQLite DB so no Docker
environment is required.
"""

from __future__ import annotations

import sqlite3
import uuid

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.backend.api.routes import projects as projects_router_module


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _inmemory_db() -> sqlite3.Connection:
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
    return conn


def _seed_critical_checks(conn: sqlite3.Connection) -> None:
    """Insert 'ok' rows for each critical check so POST /projects passes."""
    for name in ("llm", "llm_review", "sqlite", "media_dir"):
        conn.execute(
            "INSERT INTO system_status (check_name, status) VALUES (?, 'ok')",
            [name],
        )
    conn.commit()


def _seed_project(conn: sqlite3.Connection, project_id: str = "proj_test1") -> None:
    conn.execute(
        "INSERT INTO projects (project_id, title, description, current_phase, status) "
        "VALUES (?, ?, ?, 0, 'active')",
        [project_id, "Test Project", "A test project"],
    )
    conn.execute(
        "INSERT INTO phases (project_id, phase_num, phase_name, status) "
        "VALUES (?, 0, 'P0_init', 'completed')",
        [project_id],
    )
    conn.commit()


def _app(conn: sqlite3.Connection) -> FastAPI:
    app = FastAPI()
    app.dependency_overrides[projects_router_module.get_db] = lambda: conn
    app.include_router(projects_router_module.router)
    return app


# ---------------------------------------------------------------------------
# GET /api/projects
# ---------------------------------------------------------------------------

class TestListProjects:
    """Frontend apiClient.get('/api/projects') -> list of projects."""

    def test_returns_200_and_empty_list_when_no_projects(self):
        conn = _inmemory_db()
        client = TestClient(_app(conn))

        r = client.get("/api/projects")

        assert r.status_code == 200
        assert r.json() == []

    def test_returns_200_and_project_list_with_seeded_data(self):
        conn = _inmemory_db()
        _seed_project(conn, "proj_a")
        _seed_project(conn, "proj_b")
        client = TestClient(_app(conn))

        r = client.get("/api/projects")

        assert r.status_code == 200
        data = r.json()
        assert len(data) == 2
        ids = {p["id"] for p in data}
        assert ids == {"proj_a", "proj_b"}
        for p in data:
            assert "title" in p
            assert "phase" in p
            assert "status" in p

    def test_respects_order_by_updated_at_desc(self):
        conn = _inmemory_db()
        _seed_project(conn, "proj_first")
        conn.execute(
            "UPDATE projects SET updated_at = '2026-01-01T00:00:00Z' "
            "WHERE project_id = 'proj_first'"
        )
        _seed_project(conn, "proj_later")
        conn.commit()
        client = TestClient(_app(conn))

        r = client.get("/api/projects")

        data = r.json()
        assert data[0]["id"] == "proj_later"


# ---------------------------------------------------------------------------
# POST /api/projects
# ---------------------------------------------------------------------------

class TestCreateProject:
    """Frontend apiClient.post('/api/projects', body) -> created project."""

    def test_returns_201_with_valid_body(self):
        conn = _inmemory_db()
        _seed_critical_checks(conn)
        client = TestClient(_app(conn))

        r = client.post(
            "/api/projects",
            json={"title": "New Project", "description": "Desc"},
        )

        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "New Project"
        assert data["description"] == "Desc"
        assert data["id"].startswith("proj_")

    def test_returns_403_when_critical_checks_not_ok(self):
        conn = _inmemory_db()
        client = TestClient(_app(conn))

        r = client.post(
            "/api/projects",
            json={"title": "Should Fail", "description": ""},
        )

        assert r.status_code == 403

    def test_returns_422_with_empty_title(self):
        conn = _inmemory_db()
        _seed_critical_checks(conn)
        client = TestClient(_app(conn))

        r = client.post(
            "/api/projects",
            json={"title": "", "description": ""},
        )

        assert r.status_code == 422


# ---------------------------------------------------------------------------
# GET /api/projects/{id}/state
# ---------------------------------------------------------------------------

class TestGetProjectState:
    """Frontend apiClient.get('/api/projects/{id}/state') -> ProjectState."""

    def test_returns_200_with_seeded_project(self):
        conn = _inmemory_db()
        _seed_project(conn, "proj_x")
        client = TestClient(_app(conn))

        r = client.get("/api/projects/proj_x/state")

        assert r.status_code == 200
        data = r.json()
        assert data["project"]["project_id"] == "proj_x"
        assert data["project"]["title"] == "Test Project"
        assert "phases" in data
        assert len(data["phases"]) == 1
        assert data["phases"][0]["phase_num"] == 0

    def test_returns_404_for_nonexistent_project(self):
        conn = _inmemory_db()
        client = TestClient(_app(conn))

        r = client.get("/api/projects/nonexistent/state")

        assert r.status_code == 404

    def test_returns_200_and_active_tasks_is_list(self):
        conn = _inmemory_db()
        _seed_project(conn, "proj_y")
        client = TestClient(_app(conn))

        r = client.get("/api/projects/proj_y/state")

        assert r.status_code == 200
        data = r.json()
        assert isinstance(data["active_tasks"], list)
        assert "preferences" in data
        assert "system_status" in data


# ---------------------------------------------------------------------------
# POST /api/projects/{id}/preferences/confirm
# ---------------------------------------------------------------------------

class TestConfirmPreferences:
    """Frontend apiClient.post('/.../preferences/confirm') -> ok."""

    def test_returns_200_with_valid_phase(self):
        conn = _inmemory_db()
        _seed_project(conn, "proj_z")
        client = TestClient(_app(conn))

        r = client.post(
            "/api/projects/proj_z/preferences/confirm",
            json={"phase": 3, "decisions": {"tts.rate": 1.0}},
        )

        assert r.status_code == 200
        data = r.json()
        assert data["ok"] is True
        assert "confirmed_at" in data

    def test_returns_404_for_nonexistent_project(self):
        conn = _inmemory_db()
        client = TestClient(_app(conn))

        r = client.post(
            "/api/projects/ghost/preferences/confirm",
            json={"phase": 0, "decisions": {}},
        )

        assert r.status_code == 404

    def test_returns_422_for_invalid_phase(self):
        conn = _inmemory_db()
        _seed_project(conn, "proj_v")
        client = TestClient(_app(conn))

        r = client.post(
            "/api/projects/proj_v/preferences/confirm",
            json={"phase": 99, "decisions": {}},
        )

        assert r.status_code == 422
