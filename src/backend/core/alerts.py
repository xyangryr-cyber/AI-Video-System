"""Alert definitions and check logic (SPEC-B-010).

Each alert has a name, owner, thresholds, and a check function.
Checks return structured results; WARN/CRITICAL alerts emit SPEC-13B
structured log entries.
"""

from __future__ import annotations

import logging
import sqlite3
from typing import Any, Callable

log = logging.getLogger(__name__)

CheckFn = Callable[[sqlite3.Connection], dict[str, Any]]


ALERT_DEFINITIONS: list[dict[str, Any]] = [
    {
        "name": "queue_buildup",
        "owner": "infra",
        "description": "async_tasks queue depth exceeds threshold",
        "threshold_warn": 10,
        "threshold_critical": 20,
        "check": "_check_queue_buildup",
    },
    {
        "name": "cost_warn",
        "owner": "infra",
        "description": "Project LLM cost exceeds threshold",
        "threshold_warn": 15,
        "threshold_critical": 50,
        "check": "_check_cost_warn",
    },
    {
        "name": "preflight_failed",
        "owner": "infra",
        "description": "Any critical pre-flight check has failed",
        "threshold_warn": 1,
        "threshold_critical": 3,
        "check": "_check_preflight_failed",
    },
    {
        "name": "leak_scan_hit",
        "owner": "security",
        "description": "Leak scan detected un-redacted secrets",
        "threshold_warn": 1,
        "threshold_critical": 5,
        "check": "_check_leak_scan",
    },
    {
        "name": "degraded_services",
        "owner": "infra",
        "description": "Number of degraded pre-flight checks",
        "threshold_warn": 1,
        "threshold_critical": 3,
        "check": "_check_degraded_services",
    },
]


def _check_queue_buildup(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM async_tasks WHERE status = 'queued'"
    ).fetchone()
    queued = row["n"]
    oldest = conn.execute(
        "SELECT MIN(created_at) AS oldest FROM async_tasks WHERE status = 'queued'"
    ).fetchone()["oldest"]

    fired = False
    severity = "OK"
    if queued > 20:
        fired = True
        severity = "CRITICAL"
    elif queued > 10:
        fired = True
        severity = "WARN"

    return {
        "alert_name": "queue_buildup",
        "fired": fired,
        "severity": severity,
        "queued_count": queued,
        "oldest_queued": oldest,
    }


def _check_cost_warn(conn: sqlite3.Connection) -> dict[str, Any]:
    from src.backend.db.repositories.agent_call_log_repo import AgentCallLogRepository

    repo = AgentCallLogRepository(conn)
    projects = conn.execute("SELECT project_id FROM projects").fetchall()
    total_cost = 0.0
    for p in projects:
        total_cost += repo.total_cost_for_project(p["project_id"])

    fired = total_cost > 15
    return {
        "alert_name": "cost_warn",
        "fired": fired,
        "severity": "WARN" if fired else "OK",
        "total_cost_usd": round(total_cost, 4),
    }


def _check_preflight_failed(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM system_status WHERE status = 'failed'"
    ).fetchone()
    failed = row["n"]
    return {
        "alert_name": "preflight_failed",
        "fired": failed > 0,
        "severity": "CRITICAL" if failed >= 3 else ("WARN" if failed > 0 else "OK"),
        "failed_count": failed,
    }


def _check_leak_scan(conn: sqlite3.Connection) -> dict[str, Any]:
    # Leak scan is external (scripts/leak_scan.py). This check always returns
    # OK in-process; the alert fires when leak_scan.py exits non-zero via the
    # standalone alert_check.py cron runner.
    return {
        "alert_name": "leak_scan_hit",
        "fired": False,
        "severity": "OK",
        "note": "External check -- run scripts/leak_scan.py",
    }


def _check_degraded_services(conn: sqlite3.Connection) -> dict[str, Any]:
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM system_status WHERE status = 'degraded'"
    ).fetchone()
    degraded = row["n"]
    return {
        "alert_name": "degraded_services",
        "fired": degraded > 2,
        "severity": "CRITICAL" if degraded > 2 else ("WARN" if degraded > 0 else "OK"),
        "degraded_count": degraded,
    }


_CHECK_FNS: dict[str, CheckFn] = {
    "queue_buildup": _check_queue_buildup,
    "cost_warn": _check_cost_warn,
    "preflight_failed": _check_preflight_failed,
    "leak_scan_hit": _check_leak_scan,
    "degraded_services": _check_degraded_services,
}


def check_alerts(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    """Run all alert checks and return results. Firing alerts emit
    SPEC-13B structured WARN/CRITICAL logs.
    """
    results: list[dict[str, Any]] = []
    for alert_def in ALERT_DEFINITIONS:
        name = alert_def["name"]
        fn = _CHECK_FNS.get(name)
        if fn is None:
            continue
        result = fn(conn)
        result["owner"] = alert_def["owner"]
        results.append(result)

        if result.get("fired"):
            severity = result.get("severity", "WARN")
            log_fn = log.warning if severity == "WARN" else log.error
            log_fn(
                "alert.fired",
                extra={
                    "event": f"alert.{name}",
                    "severity": severity,
                    "owner": alert_def["owner"],
                    "details": result,
                },
            )

    return results
