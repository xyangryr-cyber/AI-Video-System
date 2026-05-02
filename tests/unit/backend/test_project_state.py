"""[SPEC-GAPFIX-038] Tests for GET /api/projects/{id}/state."""

from __future__ import annotations

import sqlite3

import pytest
from fastapi import HTTPException

from src.backend.api.routes.projects import get_project_state


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
    conn.execute("""
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
        )
    """)
    conn.commit()
    return conn


def _seed_project(db: sqlite3.Connection, project_id: str = "proj_001", title: str = "Test", phase: int = 2) -> None:
    db.execute(
        "INSERT INTO projects (project_id, title, description, current_phase, status) VALUES (?, ?, ?, ?, ?)",
        [project_id, title, "A test project", phase, "active"],
    )
    for pn, pname in [(0, "需求收集"), (1, "研究规划"), (2, "脚本生成")]:
        db.execute(
            "INSERT INTO phases (project_id, phase_num, phase_name, status) VALUES (?, ?, ?, ?)",
            [project_id, pn, pname, "completed" if pn < phase else "active" if pn == phase else "pending"],
        )
    db.commit()


class TestGetProjectState:
    def test_returns_404_for_unknown_project(self, db):
        with pytest.raises(HTTPException) as exc:
            get_project_state("nonexistent", db=db)
        assert exc.value.status_code == 404

    def test_returns_project_state_for_known_project(self, db):
        _seed_project(db)

        result = get_project_state("proj_001", db=db)
        assert result["project"]["project_id"] == "proj_001"
        assert result["project"]["title"] == "Test"
        assert result["project"]["current_phase"] == 2
        assert result["project"]["status"] == "active"

    def test_includes_phases_in_state(self, db):
        _seed_project(db)

        result = get_project_state("proj_001", db=db)
        assert "phases" in result
        assert len(result["phases"]) == 3
        assert result["phases"][0]["phase_num"] == 0
        assert result["phases"][0]["status"] == "completed"

    def test_includes_required_top_level_keys(self, db):
        _seed_project(db)

        result = get_project_state("proj_001", db=db)
        for key in ("project", "phases", "active_tasks", "preferences", "system_status"):
            assert key in result, f"Missing key: {key}"

    def test_uses_parameterized_query(self, db):
        _seed_project(db)
        # SQL-injection-like input should NOT crash and should return 404
        with pytest.raises(HTTPException) as exc:
            get_project_state("proj_001' OR '1'='1", db=db)
        assert exc.value.status_code == 404
