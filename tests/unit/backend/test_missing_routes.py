"""[SPEC-GAPFIX-041] Tests for 3 missing backend routes."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi.testclient import TestClient

from src.backend.api.main import app
from src.backend.api.routes.projects import get_db


def _override_get_db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE projects (
            project_id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            current_phase INTEGER NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'active',
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        )
    """)
    conn.execute(
        "INSERT INTO projects (project_id, title, description, current_phase, status) VALUES (?, ?, ?, ?, ?)",
        ["proj_001", "Test", "desc", 2, "active"],
    )
    conn.commit()
    return conn


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = _override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


class TestMaterialSupplement:
    def test_returns_404_for_unknown_project(self, client):
        resp = client.post(
            "/api/projects/nonexistent/materials/supplement",
            json={"shot_id": "shot_01", "material_type": "broll", "description": "test"},
        )
        assert resp.status_code == 404

    def test_returns_task_id_on_success(self, client):
        resp = client.post(
            "/api/projects/proj_001/materials/supplement",
            json={"shot_id": "shot_01", "material_type": "broll", "description": "test"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "task_id" in data
        assert "material_id" in data


class TestWritebackSuggestions:
    def test_returns_404_for_unknown_project(self, client):
        resp = client.get(
            "/api/projects/nonexistent/preferences/writeback-suggestions"
        )
        assert resp.status_code == 404

    def test_returns_suggestions_list(self, client):
        resp = client.get(
            "/api/projects/proj_001/preferences/writeback-suggestions"
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)


class TestPreferencesStage:
    def test_returns_404_for_unknown_project(self, client):
        resp = client.post(
            "/api/projects/nonexistent/preferences/stage",
            json={"suggestion_ids": ["s1", "s2"]},
        )
        assert resp.status_code == 404

    def test_stages_preferences_successfully(self, client):
        resp = client.post(
            "/api/projects/proj_001/preferences/stage",
            json={"suggestion_ids": ["s1", "s2"]},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["staged_count"] == 2
