"""[SPEC-GAPFIX-040] Tests for POST /api/projects/{id}/preferences/confirm."""

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


class TestConfirmPreferences:
    def test_returns_404_for_unknown_project(self, client):
        resp = client.post(
            "/api/projects/nonexistent/preferences/confirm",
            json={"phase": 2, "decisions": {"candidate_id": "cand_01", "action": "accept"}},
        )
        assert resp.status_code == 404

    def test_returns_200_for_valid_request(self, client):
        resp = client.post(
            "/api/projects/proj_001/preferences/confirm",
            json={"phase": 2, "decisions": {"candidate_id": "cand_01", "action": "accept"}},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert "confirmed_at" in data

    def test_returns_422_for_missing_phase(self, client):
        resp = client.post(
            "/api/projects/proj_001/preferences/confirm",
            json={"decisions": {"candidate_id": "cand_01"}},
        )
        assert resp.status_code == 422

    def test_returns_422_for_missing_decisions(self, client):
        resp = client.post(
            "/api/projects/proj_001/preferences/confirm",
            json={"phase": 2},
        )
        assert resp.status_code == 422
