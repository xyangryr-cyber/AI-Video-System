"""[SPEC-G-000e] Unit tests for AgentCallLogger.

AC-1: Every worker task execution (success or failure) writes 1 row to
agent_call_log with HARNESS §8.1 fields.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


@pytest.fixture
def logger_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    migration_path = (
        Path(__file__).parents[3]
        / "src"
        / "backend"
        / "db"
        / "migrations"
        / "001_initial.sql"
    )
    conn.executescript(migration_path.read_text())
    return conn


@pytest.fixture
def logger(logger_db):
    from src.backend.services.agent_call_logger import AgentCallLogger

    return AgentCallLogger(conn=logger_db)


class TestLogWrittenOnSuccess:
    def test_inserts_row_on_success(self, logger, logger_db):
        logger.log_call(
            agent_name="TTSAgent",
            duration_ms=1234,
            tokens=500,
            model="test-model",
            input_summary="select voice candidates",
            output_summary="timeline built",
            phase=4,
            project_id="proj-test",
        )

        rows = logger_db.execute(
            "SELECT * FROM agent_call_log WHERE agent_name = ?",
            ("TTSAgent",),
        ).fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row["agent_name"] == "TTSAgent"
        assert row["duration_ms"] == 1234
        assert row["tokens"] == 500
        assert row["model"] == "test-model"
        assert row["prompt"] == "select voice candidates"
        assert row["response"] == "timeline built"
        assert row["phase"] == 4
        assert row["project_id"] == "proj-test"

    def test_inserts_row_on_failure_scenario(self, logger, logger_db):
        logger.log_call(
            agent_name="TTSAgent",
            duration_ms=567,
            tokens=0,
            model="test-model",
            input_summary="select voice candidates",
            output_summary="error: agent execution failed",
            phase=4,
            project_id="proj-test",
        )

        rows = logger_db.execute(
            "SELECT * FROM agent_call_log WHERE agent_name = ?",
            ("TTSAgent",),
        ).fetchall()
        assert len(rows) == 1
        row = rows[0]
        assert row["duration_ms"] == 567
        assert row["response"] == "error: agent execution failed"

    def test_defaults_phase_and_project_to_none(self, logger, logger_db):
        logger.log_call(
            agent_name="BGMAgent",
            duration_ms=100,
            tokens=1,
            model="test-model",
            input_summary="",
            output_summary="",
        )

        row = logger_db.execute(
            "SELECT phase, project_id FROM agent_call_log WHERE agent_name = ?",
            ("BGMAgent",),
        ).fetchone()
        assert row["phase"] is None
        assert row["project_id"] is None

    def test_multiple_calls_produce_multiple_rows(self, logger, logger_db):
        for i in range(3):
            logger.log_call(
                agent_name=f"Agent{i}",
                duration_ms=i * 100,
                tokens=(i + 1) * 10,
                model="test-model",
                input_summary=f"input {i}",
                output_summary=f"output {i}",
            )

        count = logger_db.execute("SELECT COUNT(*) FROM agent_call_log").fetchone()[0]
        assert count == 3

    def test_tokens_coerced_to_positive_for_check_constraint(self, logger, logger_db):
        logger.log_call(
            agent_name="TestAgent",
            duration_ms=100,
            tokens=0,
            model="test-model",
            input_summary="",
            output_summary="",
        )

        row = logger_db.execute(
            "SELECT tokens FROM agent_call_log WHERE agent_name = ?",
            ("TestAgent",),
        ).fetchone()
        assert row["tokens"] >= 1
