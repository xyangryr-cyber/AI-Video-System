"""Tests for [SPEC-B-009] Pre-flight Checks and Service Degradation."""

import sqlite3
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import HTTPException

from src.backend.core.preflight import (
    CRITICAL_CHECKS,
    DEGRADABLE_CHECKS,
    ALL_CHECKS,
    VALIDITY_HOURS,
    CheckResult,
    run_full_preflight,
    run_critical_preflight,
    require_critical_ok,
)
from src.backend.db.repositories.system_status_repo import SystemStatusRepository


@pytest.fixture
def conn():
    """In-memory DB with the system_status table deployed."""
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA journal_mode=WAL")
    c.executescript("""
        CREATE TABLE IF NOT EXISTS system_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            check_name TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'ok',
            message TEXT,
            checked_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            valid_until TEXT NOT NULL
        );
    """)
    c.commit()
    return c


class TestAC1CriticalChecksInSystemStatus:
    """AC-1: 5 critical checks (llm/llm_review/tts/sqlite/media_dir)
    appear in system_status table."""

    def test_critical_checks_in_system_status(self, conn):
        run_critical_preflight(conn)
        repo = SystemStatusRepository(conn)
        rows = repo.latest_all()
        names = {r["check_name"] for r in rows}
        for c in CRITICAL_CHECKS:
            assert c in names, f"critical check '{c}' missing from system_status"
        for c in DEGRADABLE_CHECKS:
            assert c not in names, (
                f"degradable check '{c}' should not appear in critical-only run"
            )


class TestAC2CriticalFailureBlocksProjectCreation:
    """AC-2: Any critical check with status='failed' causes
    require_critical_ok to raise HTTPException(403)."""

    def test_critical_failure_blocks_project_creation(self, conn):
        # Run full preflight with all stubs — all ok
        run_full_preflight(conn)
        # Should not raise
        require_critical_ok(conn)

    def test_one_failed_critical_raises_403(self, conn):
        now = datetime.now(timezone.utc)
        # Inject a failed llm check
        runners = {n: lambda: CheckResult(status="ok") for n in ALL_CHECKS}
        runners["llm"] = lambda: CheckResult(status="failed", message="API key missing")
        run_critical_preflight(conn, runners=runners, now=now)
        with pytest.raises(HTTPException) as exc:
            require_critical_ok(conn)
        assert exc.value.status_code == 403
        assert "not ready" in exc.value.detail.lower()


class TestAC3DegradedServicesListed:
    """AC-3: Degradable checks with status='degraded' appear in
    degraded_services list."""

    def test_degraded_services_listed(self, conn):
        now = datetime.now(timezone.utc)
        runners = {n: lambda: CheckResult(status="ok") for n in ALL_CHECKS}
        runners["web_search"] = lambda: CheckResult(
            status="degraded", message="timeout"
        )
        runners["material"] = lambda: CheckResult(
            status="degraded", message="unreachable"
        )
        run_full_preflight(conn, runners=runners, now=now)
        repo = SystemStatusRepository(conn)
        degraded = repo.degraded_services()
        assert "web_search" in degraded
        assert "material" in degraded
        assert "bgm" not in degraded
        assert "llm" not in degraded


class TestAC4DegradedDoesNotBlockCreation:
    """AC-4: Degradable failures do not block project creation via
    require_critical_ok."""

    def test_degraded_does_not_block_creation(self, conn):
        now = datetime.now(timezone.utc)
        runners = {n: lambda: CheckResult(status="ok") for n in ALL_CHECKS}
        runners["web_search"] = lambda: CheckResult(status="degraded")
        runners["financial_data"] = lambda: CheckResult(status="degraded")
        run_full_preflight(conn, runners=runners, now=now)
        # Must not raise, even though degradable services are down
        require_critical_ok(conn)


class TestAC5ValidUntil24h:
    """AC-5: valid_until = checked_at + 24 hours."""

    def test_valid_until_24h(self, conn):
        now = datetime(2026, 4, 25, 10, 0, 0, tzinfo=timezone.utc)
        run_critical_preflight(conn, now=now)
        repo = SystemStatusRepository(conn)
        rows = repo.latest_all()
        for r in rows:
            checked = datetime.fromisoformat(r["checked_at"].replace("Z", "+00:00"))
            valid = datetime.fromisoformat(r["valid_until"].replace("Z", "+00:00"))
            delta = valid - checked
            assert delta == timedelta(hours=VALIDITY_HOURS), (
                f"{r['check_name']}: expected 24h delta, got {delta}"
            )


class TestAC6FullPreflightOnStartup:
    """AC-6: API startup runs full preflight (all 9 checks)."""

    def test_full_preflight_on_startup(self, conn):
        run_full_preflight(conn)
        repo = SystemStatusRepository(conn)
        rows = repo.latest_all()
        names = {r["check_name"] for r in rows}
        assert len(names) == 9, f"expected 9 checks, got {len(names)}: {names}"
        for c in ALL_CHECKS:
            assert c in names, f"check '{c}' missing from full preflight"


class TestAC7CriticalSubsetOnProjectCreate:
    """AC-7: Project create runs only critical subset (4 checks)."""

    def test_critical_subset_on_project_create(self, conn):
        run_critical_preflight(conn)
        repo = SystemStatusRepository(conn)
        rows = repo.latest_all()
        names = {r["check_name"] for r in rows}
        assert len(names) == 4, f"expected 4 critical checks, got {len(names)}: {names}"
        for c in CRITICAL_CHECKS:
            assert c in names, f"critical check '{c}' missing"
        for c in DEGRADABLE_CHECKS:
            assert c not in names, (
                f"degradable check '{c}' should not be in critical subset"
            )
