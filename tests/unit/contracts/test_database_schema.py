"""Tests for [SPEC-A-007] SQLite Database Schema DDL (10 Tables).

Verifies SPEC-1B DDL contract: 10 tables, CHECK / UNIQUE / FK constraints,
default timestamp format, and task_ledger.params schema validation per type.
"""

from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"
MIGRATION_PATH = REPO_ROOT / "src" / "backend" / "db" / "migrations" / "001_initial.sql"

EXPECTED_TABLES = {
    "projects",
    "phases",
    "task_ledger",
    "async_tasks",
    "events",
    "preferences",
    "agent_call_log",
    "system_status",
    "financial_data_cache",
    "preference_snapshots",
}

EXPECTED_TASK_TYPES = {
    "generate_artifact",
    "regenerate_section",
    "user_revision",
    "review",
    "research",
    "verify",
    "cross_check",
    "user_annotation",
}

EXPECTED_TASK_STATUSES = {
    "pending",
    "queued",
    "running",
    "succeeded",
    "failed",
    "superseded",
    "timeout",
}


def _load_conn() -> sqlite3.Connection:
    """Load the authoritative DDL into an in-memory SQLite with FK enforcement."""
    assert SCHEMA_PATH.exists(), f"schema.sql missing at {SCHEMA_PATH}"
    ddl = SCHEMA_PATH.read_text(encoding="utf-8")
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(ddl)
    return conn


def _seed_project(conn: sqlite3.Connection, project_id: str = "proj_test") -> None:
    conn.execute(
        "INSERT INTO projects (project_id, title, description) VALUES (?, ?, ?)",
        (project_id, "t", "d"),
    )


class TestAC1Exactly10Tables:
    """AC-1: DDL defines exactly 10 tables with names matching spec."""

    def test_exactly_10_tables(self) -> None:
        conn = _load_conn()
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        names = {r[0] for r in rows}
        assert names == EXPECTED_TABLES, (
            f"expected {sorted(EXPECTED_TABLES)}, got {sorted(names)}"
        )


class TestAC2ProjectsStatusCheck:
    """AC-2: projects.status CHECK constraint enforces 4 allowed values."""

    def test_projects_status_check(self) -> None:
        conn = _load_conn()
        for ok in ("active", "completed", "archived", "deleted"):
            conn.execute(
                "INSERT INTO projects (project_id, title, description, status) "
                "VALUES (?, ?, ?, ?)",
                (f"proj_{ok}", "t", "d", ok),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO projects (project_id, title, description, status) "
                "VALUES (?, ?, ?, ?)",
                ("proj_bad", "t", "d", "bogus"),
            )


class TestAC3PhasesStatusCheck:
    """AC-3: phases.status CHECK enforces 5 allowed values."""

    def test_phases_status_check(self) -> None:
        conn = _load_conn()
        _seed_project(conn)
        allowed = ("pending", "active", "completed", "skipped", "invalidated")
        for i, status in enumerate(allowed):
            conn.execute(
                "INSERT INTO phases (project_id, phase_num, phase_name, status) "
                "VALUES (?, ?, ?, ?)",
                ("proj_test", i, f"P{i}", status),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO phases (project_id, phase_num, phase_name, status) "
                "VALUES (?, ?, ?, ?)",
                ("proj_test", 9, "P9", "bogus"),
            )


class TestAC4PhasesUniqueProjectPhase:
    """AC-4: phases has UNIQUE(project_id, phase_num) constraint."""

    def test_phases_unique_project_phase(self) -> None:
        conn = _load_conn()
        _seed_project(conn)
        conn.execute(
            "INSERT INTO phases (project_id, phase_num, phase_name) VALUES (?, ?, ?)",
            ("proj_test", 0, "P0"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO phases (project_id, phase_num, phase_name) VALUES (?, ?, ?)",
                ("proj_test", 0, "P0"),
            )


class TestAC5TaskLedgerTypeCheck:
    """AC-5: task_ledger.type CHECK enforces all 8 task types."""

    def test_task_ledger_type_check(self) -> None:
        conn = _load_conn()
        _seed_project(conn)
        for i, t in enumerate(sorted(EXPECTED_TASK_TYPES)):
            conn.execute(
                "INSERT INTO task_ledger (id, project_id, phase, type) "
                "VALUES (?, ?, ?, ?)",
                (f"t_{i:06d}", "proj_test", 0, t),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO task_ledger (id, project_id, phase, type) "
                "VALUES (?, ?, ?, ?)",
                ("t_999999", "proj_test", 0, "unknown_type"),
            )


class TestAC6TaskLedgerStatusCheck:
    """AC-6: task_ledger.status CHECK enforces all 7 statuses."""

    def test_task_ledger_status_check(self) -> None:
        conn = _load_conn()
        _seed_project(conn)
        for i, s in enumerate(sorted(EXPECTED_TASK_STATUSES)):
            conn.execute(
                "INSERT INTO task_ledger (id, project_id, phase, type, status) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"t_{i:06d}", "proj_test", 0, "research", s),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO task_ledger (id, project_id, phase, type, status) "
                "VALUES (?, ?, ?, ?, ?)",
                ("t_999999", "proj_test", 0, "research", "bogus"),
            )


class TestAC7AsyncTasksProgressCheck:
    """AC-7: async_tasks.progress CHECK enforces BETWEEN 0 AND 100."""

    def test_async_tasks_progress_check(self) -> None:
        conn = _load_conn()
        _seed_project(conn)
        for i, p in enumerate((0, 50, 100)):
            conn.execute(
                "INSERT INTO async_tasks (task_id, project_id, phase, type, progress) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"async_{i}", "proj_test", 4, "tts", p),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO async_tasks (task_id, project_id, phase, type, progress) "
                "VALUES (?, ?, ?, ?, ?)",
                ("async_bad_hi", "proj_test", 4, "tts", 101),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO async_tasks (task_id, project_id, phase, type, progress) "
                "VALUES (?, ?, ?, ?, ?)",
                ("async_bad_lo", "proj_test", 4, "tts", -1),
            )


class TestAC8AgentCallLogTokensCheck:
    """AC-8: agent_call_log.tokens CHECK enforces tokens > 0."""

    def test_agent_call_log_tokens_check(self) -> None:
        conn = _load_conn()
        conn.execute(
            "INSERT INTO agent_call_log (agent_name, tokens, duration_ms, model, "
            "prompt, response) VALUES (?, ?, ?, ?, ?, ?)",
            ("ScriptAgent", 100, 1234, "gpt-5", "p", "r"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO agent_call_log (agent_name, tokens, duration_ms, model, "
                "prompt, response) VALUES (?, ?, ?, ?, ?, ?)",
                ("ScriptAgent", 0, 100, "gpt-5", "p", "r"),
            )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO agent_call_log (agent_name, tokens, duration_ms, model, "
                "prompt, response) VALUES (?, ?, ?, ?, ?, ?)",
                ("ScriptAgent", -1, 100, "gpt-5", "p", "r"),
            )


class TestAC9FinancialCacheUniqueConstraint:
    """AC-9: financial_data_cache UNIQUE(symbol, granularity, start, end)."""

    def test_financial_cache_unique_constraint(self) -> None:
        conn = _load_conn()
        conn.execute(
            "INSERT INTO financial_data_cache "
            "(symbol, granularity, date_range_start, date_range_end, "
            "data_json, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("XAUUSD", "daily", "2025-01-01", "2025-01-31", "{}", "2026-02-01"),
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO financial_data_cache "
                "(symbol, granularity, date_range_start, date_range_end, "
                "data_json, expires_at) VALUES (?, ?, ?, ?, ?, ?)",
                ("XAUUSD", "daily", "2025-01-01", "2025-01-31", "{}", "2026-02-01"),
            )


class TestAC10TimestampDefaults:
    """AC-10: All timestamp defaults use strftime('%Y-%m-%dT%H:%M:%fZ','now')."""

    def test_timestamp_defaults(self) -> None:
        ddl = SCHEMA_PATH.read_text(encoding="utf-8")
        # Expected default-timestamp columns per SPEC-1B:
        # projects(created_at, updated_at); phases(created_at, updated_at);
        # task_ledger(created_at, updated_at); async_tasks(created_at);
        # events(timestamp); preferences(updated_at); agent_call_log(created_at);
        # system_status(checked_at); financial_data_cache(fetched_at);
        # preference_snapshots(created_at) -> 13 total.
        expected = 13
        needle = "strftime('%Y-%m-%dT%H:%M:%fZ','now')"
        count = ddl.count(needle)
        assert count == expected, (
            f"expected exactly {expected} occurrences of timestamp default, got {count}"
        )
        # Round-trip: inserted row receives the expected format.
        conn = _load_conn()
        _seed_project(conn, "proj_ts")
        row = conn.execute(
            "SELECT created_at FROM projects WHERE project_id='proj_ts'"
        ).fetchone()
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", row[0]), (
            f"timestamp format mismatch: {row[0]}"
        )


class TestAC11TaskParamsAll8Types:
    """AC-11: task_params validation module covers all 8 type-specific param schemas."""

    def test_task_params_all_8_types(self) -> None:
        from pydantic import ValidationError

        from src.shared.schemas.task_params import (
            TASK_PARAMS_REGISTRY,
            validate_task_params,
        )

        assert set(TASK_PARAMS_REGISTRY.keys()) == EXPECTED_TASK_TYPES

        valid = {
            "generate_artifact": {
                "phase_name": "P2",
                "input_refs": ["phase_1/outline_v1.json"],
            },
            "regenerate_section": {
                "phase_name": "P3",
                "section_id": "seg_03",
                "instruction": "语气更激昂",
            },
            "user_revision": {"phase_name": "P2", "revision_text": "..."},
            "review": {
                "phase_name": "P3",
                "reviewer_name": "StyleReviewer",
                "artifact_path": "phase_3/script_v2.md",
            },
            "research": {"query": "2025年黄金价格", "max_sources": 5},
            "verify": {
                "data_point_id": "dp_12",
                "claimed_value": "3421.5",
                "source_url": "https://example.com",
            },
            "cross_check": {
                "left_ref": "phase_2/script.md",
                "right_ref": "phase_7/storyboard.json",
                "check_fields": ["numbers", "names"],
            },
            "user_annotation": {"frame": 450, "time_sec": 15.0, "text": "加强语气"},
        }
        assert set(valid.keys()) == EXPECTED_TASK_TYPES
        for t, payload in valid.items():
            assert validate_task_params(t, payload) is not None

        with pytest.raises(ValidationError):
            validate_task_params("generate_artifact", {"phase_name": "P2"})
        with pytest.raises(ValidationError):
            validate_task_params("research", {})
        with pytest.raises(ValidationError):
            validate_task_params("research", {"query": "x", "max_sources": 2})
        with pytest.raises(ValidationError):
            validate_task_params("research", {"query": "x", "max_sources": 6})

        with pytest.raises(KeyError):
            validate_task_params("not_a_type", {})


class TestAC12DdlLoadsSuccessfully:
    """AC-12: Loading DDL into in-memory SQLite succeeds without errors."""

    def test_ddl_loads_successfully(self) -> None:
        _load_conn()
        assert MIGRATION_PATH.exists(), f"migration missing at {MIGRATION_PATH}"
        mig_ddl = MIGRATION_PATH.read_text(encoding="utf-8")
        conn = sqlite3.connect(":memory:")
        conn.executescript(mig_ddl)
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' "
            "AND name NOT LIKE 'sqlite_%'"
        ).fetchall()
        assert {r[0] for r in rows} == EXPECTED_TABLES
