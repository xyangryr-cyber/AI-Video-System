"""Tests for [SPEC-B-010] observability -- four evidence types.

Real assertions for AC-1 (four evidence types return non-empty) and
AC-2 (phase consistency with events).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    return c


def _insert_project(conn: sqlite3.Connection, pid: str = "proj_a") -> None:
    conn.execute(
        "INSERT INTO projects (project_id, title, description) VALUES (?,?,?)",
        (pid, "Test", "test"),
    )


class TestAC1FourEvidenceTypesNonEmpty:
    def test_four_evidence_types_non_empty(self, conn: sqlite3.Connection):
        """Four evidence types (status, events, llm_audit, artifacts) each return data."""
        _insert_project(conn)
        from src.backend.core.observability import Observability

        obs = Observability(conn)

        # Type 1: system status
        conn.execute(
            "INSERT INTO system_status (check_name, status, message, valid_until) "
            "VALUES (?, ?, ?, ?)",
            ("db_ok", "ok", "db reachable", "2099-01-01T00:00:00Z"),
        )
        conn.commit()

        status = obs.get_system_status()
        assert isinstance(status, list)
        assert len(status) > 0
        assert status[0]["check_name"] == "db_ok"

        # Type 2: events
        conn.execute(
            "INSERT INTO events (project_id, type, payload) VALUES (?, ?, ?)",
            ("proj_a", "phase.entered", '{"phase": 1}'),
        )
        conn.commit()

        events = obs.get_events("proj_a")
        assert isinstance(events, list)
        assert len(events) > 0
        assert events[0]["type"] == "phase.entered"

        # Type 3: LLM audit
        conn.execute(
            "INSERT INTO agent_call_log "
            "(agent_name, tokens, duration_ms, phase, project_id, model, prompt, response) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            ("TestAgent", 100, 200, 1, "proj_a", "m", "p", "r"),
        )
        conn.commit()

        audit = obs.get_llm_audit("proj_a")
        assert isinstance(audit, list)
        assert len(audit) > 0
        assert audit[0]["agent_name"] == "TestAgent"

        # Type 4: artifacts (phases with artifact_path)
        conn.execute(
            "INSERT INTO phases (project_id, phase_num, phase_name, status, artifact_path) "
            "VALUES (?, ?, ?, ?, ?)",
            ("proj_a", 1, "P1 Script", "completed", "/tmp/test.mp4"),
        )
        conn.commit()

        artifacts = obs.get_artifacts("proj_a")
        assert isinstance(artifacts, list)
        assert len(artifacts) > 0


class TestAC2PhaseConsistencyWithEvents:
    def test_phase_consistency_with_events(self, conn: sqlite3.Connection):
        """Current phase matches the latest phase.entered event."""
        _insert_project(conn)
        from src.backend.core.observability import Observability

        conn.execute(
            "INSERT INTO events (project_id, type, payload) VALUES (?, ?, ?)",
            ("proj_a", "phase.entered", '{"phase_num": 3}'),
        )
        conn.execute(
            "INSERT INTO events (project_id, type, payload) VALUES (?, ?, ?)",
            ("proj_a", "phase.entered", '{"phase_num": 5}'),
        )
        conn.execute(
            "UPDATE projects SET current_phase = 5 WHERE project_id = ?",
            ("proj_a",),
        )
        conn.commit()

        obs = Observability(conn)
        result = obs.check_phase_consistency("proj_a")
        assert result["consistent"] is True
        assert result["current_phase"] == 5
        assert result["latest_event_phase"] == 5
