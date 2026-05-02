"""[SPEC-GAPFIX-037] Tests for GET /api/projects."""

from __future__ import annotations

import sqlite3

import pytest

from src.backend.api.routes.projects import list_projects


@pytest.fixture
def db() -> sqlite3.Connection:
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
    conn.commit()
    return conn


class TestListProjects:
    def test_returns_empty_array_when_no_projects(self, db):
        result = list_projects(db=db)
        assert result == []

    def test_returns_all_projects(self, db):
        db.execute(
            "INSERT INTO projects (project_id, title, description, current_phase, status) VALUES (?, ?, ?, ?, ?)",
            ["proj_001", "Test Project", "A test", 2, "active"],
        )
        db.execute(
            "INSERT INTO projects (project_id, title, description, current_phase, status) VALUES (?, ?, ?, ?, ?)",
            ["proj_002", "Archived", "Archived project", 5, "archived"],
        )
        db.commit()

        result = list_projects(db=db)
        assert len(result) == 2
        assert result[0]["id"] == "proj_001"
        assert result[0]["title"] == "Test Project"
        assert result[0]["phase"] == 2
        assert result[1]["id"] == "proj_002"
        assert result[1]["status"] == "archived"

    def test_response_fields_match_spec(self, db):
        db.execute(
            "INSERT INTO projects (project_id, title, description, current_phase, status) VALUES (?, ?, ?, ?, ?)",
            ["proj_003", "Fields Check", "Check all fields", 0, "active"],
        )
        db.commit()

        result = list_projects(db=db)
        item = result[0]
        assert "id" in item
        assert "title" in item
        assert "description" in item
        assert "phase" in item
        assert "status" in item
        assert "updated_at" in item
