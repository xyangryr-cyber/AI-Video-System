"""[RED] Tests for TaskLedgerRepository before implementation exists."""

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


class TestTaskLedgerRepository:
    """RED: TaskLedgerRepository.update_result_ref writes to task_ledger."""

    def test_update_result_ref_writes_json(self, conn):
        from src.backend.db.repositories.task_ledger_repository import (
            TaskLedgerRepository,
        )

        conn.execute(
            "INSERT INTO task_ledger(id, project_id, phase, type, status) "
            "VALUES ('task_001', 'proj_t', 1, 'research', 'pending')"
        )
        conn.commit()

        repo = TaskLedgerRepository(conn)
        repo.update_result_ref("task_001", '{"sources":["a","b"]}')

        row = conn.execute(
            "SELECT result_ref FROM task_ledger WHERE id = 'task_001'"
        ).fetchone()
        assert row is not None
        assert row["result_ref"] == '{"sources":["a","b"]}'
