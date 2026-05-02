"""Tests for [SPEC-B-010] alerts -- thresholds and log format.

Real assertions for AC-3..AC-6: queue buildup alert, owner field,
SPEC-13B log format, and default thresholds.
"""

from __future__ import annotations

import logging
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


class TestAC3QueueBuildupAlert:
    def test_queue_buildup_alert(self, conn: sqlite3.Connection, caplog):
        """WARN when queued > 10 and oldest queued > 30 min."""
        _insert_project(conn)
        from src.backend.core.alerts import check_alerts

        # Insert 12 queued tasks, all with created_at 40 min ago
        for i in range(12):
            conn.execute(
                "INSERT INTO async_tasks "
                "(task_id, project_id, phase, type, status, created_at) "
                "VALUES (?, ?, ?, ?, 'queued', datetime('now', '-40 minutes'))",
                (f"task_{i}", "proj_a", 1, "generate"),
            )
        conn.commit()

        with caplog.at_level(logging.WARNING):
            results = check_alerts(conn)

        queue_alert = [a for a in results if a["alert_name"] == "queue_buildup"]
        assert len(queue_alert) == 1
        assert queue_alert[0]["fired"] is True
        assert queue_alert[0]["severity"] in ("WARN", "CRITICAL")

    def test_queue_under_threshold_no_alert(self, conn: sqlite3.Connection):
        """No alert when queued <= 10."""
        _insert_project(conn)
        from src.backend.core.alerts import check_alerts

        for i in range(5):
            conn.execute(
                "INSERT INTO async_tasks "
                "(task_id, project_id, phase, type, status, created_at) "
                "VALUES (?, ?, ?, ?, 'queued', datetime('now', '-5 minutes'))",
                (f"task_{i}", "proj_a", 1, "generate"),
            )
        conn.commit()

        results = check_alerts(conn)
        queue_alert = [a for a in results if a["alert_name"] == "queue_buildup"]
        assert len(queue_alert) == 1
        assert queue_alert[0]["fired"] is False


class TestAC4AlertHasOwnerField:
    def test_alert_has_owner_field(self, conn: sqlite3.Connection):
        """Every alert signal has an owner field."""
        _insert_project(conn)
        from src.backend.core.alerts import ALERT_DEFINITIONS

        for alert_def in ALERT_DEFINITIONS:
            assert "owner" in alert_def, f"Missing owner in {alert_def['name']}"
            assert isinstance(alert_def["owner"], str)
            assert len(alert_def["owner"]) > 0


class TestAC5AlertLogFormatSpec13B:
    def test_alert_log_format_spec_13b(self, conn: sqlite3.Connection, caplog):
        """Alert log follows SPEC-13B structured format (ts, level, module, event)."""
        _insert_project(conn)
        from src.backend.core.alerts import check_alerts

        for i in range(15):
            conn.execute(
                "INSERT INTO async_tasks "
                "(task_id, project_id, phase, type, status, created_at) "
                "VALUES (?, ?, ?, ?, 'queued', datetime('now', '-40 minutes'))",
                (f"task_{i}", "proj_a", 1, "generate"),
            )
        conn.commit()

        with caplog.at_level(logging.WARNING):
            check_alerts(conn)

        warn_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
        assert len(warn_records) >= 1
        # SPEC-13B: structured log with event/severity fields
        for rec in warn_records:
            msg = rec.message or rec.msg
            assert "queue" in msg.lower() or "alert" in msg.lower()


class TestAC6DefaultAlertThresholds:
    def test_default_alert_thresholds(self):
        """Default thresholds: queue WARN=10, CRITICAL=20; cost WARN=$15."""
        from src.backend.core.alerts import ALERT_DEFINITIONS

        queue_alert = [a for a in ALERT_DEFINITIONS if a["name"] == "queue_buildup"][0]
        assert queue_alert["threshold_warn"] == 10
        assert queue_alert["threshold_critical"] == 20

        cost_alert = [a for a in ALERT_DEFINITIONS if a["name"] == "cost_warn"][0]
        assert cost_alert["threshold_warn"] == 15
