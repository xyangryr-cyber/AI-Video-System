"""Tests for migration runner."""

import sqlite3
import tempfile
from pathlib import Path

from src.backend.db.migration_runner import run_migrations


def test_run_migrations_creates_all_tables():
    """After running migrations, all 10 tables should exist."""
    db_path = Path(tempfile.mkdtemp()) / "test.sqlite3"
    conn = sqlite3.connect(str(db_path))

    migrations_dir = Path("src/backend/db/migrations")
    run_migrations(conn, migrations_dir)

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    ).fetchall()
    table_names = {r[0] for r in tables}

    expected = {
        "projects", "phases", "task_ledger", "async_tasks", "events",
        "preferences", "agent_call_log", "system_status",
        "financial_data_cache", "preference_snapshots",
    }
    missing = expected - table_names
    assert not missing, f"Missing tables: {missing}"


def test_run_migrations_idempotent():
    """Running migrations twice should not crash."""
    db_path = Path(tempfile.mkdtemp()) / "test.sqlite3"
    conn = sqlite3.connect(str(db_path))

    migrations_dir = Path("src/backend/db/migrations")
    run_migrations(conn, migrations_dir)
    run_migrations(conn, migrations_dir)  # second run

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    # Exclude internal SQLite tables (e.g. sqlite_sequence from AUTOINCREMENT)
    expected_tables = {
        "projects", "phases", "task_ledger", "async_tasks", "events",
        "preferences", "agent_call_log", "system_status",
        "financial_data_cache", "preference_snapshots",
    }
    table_names = {r[0] for r in tables}
    app_tables = expected_tables & table_names
    assert len(app_tables) == 10, f"Got {len(app_tables)} tables: {app_tables}"


def test_run_migrations_empty_dir():
    """Empty migrations directory should not crash."""
    db_path = Path(tempfile.mkdtemp()) / "test.sqlite3"
    conn = sqlite3.connect(str(db_path))

    empty_dir = Path(tempfile.mkdtemp())
    run_migrations(conn, empty_dir)

    tables = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    assert len(tables) == 0
