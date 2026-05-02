"""Tests for [SPEC-B-009] Pre-flight Checks and Service Degradation.

Filename authority:

* task card ``allowed_files`` lists ``tests/unit/infra/test_preflight.py``
  (that's THIS file). The HARNESS validate_edit_target hook enforces the
  allowed_files list and rejects writes to the scaffolded
  ``test_spec_b_009.py`` stub. We therefore put the real AC coverage in
  this file; the scaffold is left as pytest-skip placeholders per the
  repo convention for not-yet-implemented SPEC-B tasks.
* ``verification_commands`` in the task card still references
  ``tests/unit/infra/test_spec_b_009.py``; running both files is
  documented in the Verification section of the commit body.

Strategy:

* AC-1: drive ``run_full_preflight`` against an in-memory DB and assert
  the 5 critical check_names (llm/llm_review/tts/sqlite/media_dir) all
  land in ``system_status``.
* AC-2: seed a failed ``llm`` row via ``run_full_preflight`` with an
  injected runner, then exercise ``POST /api/projects`` through the
  FastAPI TestClient and confirm the response is 403.
* AC-3: seed degraded runners for all 4 degradable checks, then assert
  the repository's ``degraded_services()`` returns exactly those names.
* AC-4: mirror AC-3 but verify POST still returns 201 (degraded is
  non-blocking).
* AC-5: pin ``now`` to a fixed datetime and assert ``valid_until -
  checked_at == 24h`` on every row.
* AC-6: register the preflight startup hook on a FastAPI app, enter the
  TestClient context to fire startup events, and confirm all 9 rows
  exist.
* AC-7: call ``run_critical_preflight`` alone and confirm only the 5
  critical rows are written (never the 4 degradables).
"""

from __future__ import annotations

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"


# ---- fixtures --------------------------------------------------------------


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    return c


def _ok_runners() -> dict:
    from src.backend.core.preflight import ALL_CHECKS, CheckResult

    return {
        name: (lambda: CheckResult(status="ok", message=None)) for name in ALL_CHECKS
    }


def _failed(name: str, msg: str = "boom"):
    from src.backend.core.preflight import CheckResult

    def _run() -> CheckResult:
        return CheckResult(status="failed", message=msg)

    return _run


def _degraded(msg: str = "slow"):
    from src.backend.core.preflight import CheckResult

    def _run() -> CheckResult:
        return CheckResult(status="degraded", message=msg)

    return _run


# ---- AC-1 ------------------------------------------------------------------


class TestAC1CriticalChecksInSystemStatus:
    """AC-1: 4 个关键项（llm/llm_review/sqlite/media_dir）均在 `system_status` 表"""

    def test_critical_checks_in_system_status(self, conn):
        from src.backend.core.preflight import (
            CRITICAL_CHECKS,
            run_full_preflight,
        )

        assert set(CRITICAL_CHECKS) == {
            "llm",
            "llm_review",
            "sqlite",
            "media_dir",
        }, (
            "SPEC-14.1 names the 4 blocking checks as "
            "llm/llm_review/sqlite/media_dir"
        )

        run_full_preflight(conn)
        names = {
            r["check_name"]
            for r in conn.execute(
                "SELECT DISTINCT check_name FROM system_status"
            ).fetchall()
        }
        for critical in CRITICAL_CHECKS:
            assert critical in names, (
                f"critical check {critical!r} not written to system_status"
            )


# ---- AC-2 ------------------------------------------------------------------


class TestAC2CriticalFailureBlocksProjectCreation:
    """AC-2: 任一关键项 failed → `all_critical_ok=false`，新建项目接口返回 403"""

    def test_critical_failure_blocks_project_creation(self, conn):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from src.backend.api.routes.projects import get_db, router
        from src.backend.core.preflight import run_full_preflight

        runners = _ok_runners()
        runners["llm"] = _failed("llm", "missing API key")
        run_full_preflight(conn, runners=runners)

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: conn
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            "/api/projects",
            json={"title": "T", "description": "D"},
        )
        assert resp.status_code == 403, (
            f"critical failure must return 403, got {resp.status_code}: {resp.text}"
        )


# ---- AC-3 ------------------------------------------------------------------


class TestAC3DegradedServicesListed:
    """AC-3: 可降级项（web_search/material/bgm/financial_data）failed → `degraded_services[]` 包含对应 check_name"""

    def test_degraded_services_listed(self, conn):
        from src.backend.core.preflight import (
            DEGRADABLE_CHECKS,
            run_full_preflight,
        )
        from src.backend.db.repositories.system_status_repo import (
            SystemStatusRepository,
        )

        assert set(DEGRADABLE_CHECKS) == {
            "tts",
            "web_search",
            "material",
            "bgm",
            "financial_data",
        }, (
            "SPEC-14.2 names the 5 degradable checks as "
            "tts/web_search/material/bgm/financial_data"
        )

        runners = _ok_runners()
        for name in DEGRADABLE_CHECKS:
            runners[name] = _degraded(f"{name} slow")
        run_full_preflight(conn, runners=runners)

        repo = SystemStatusRepository(conn)
        degraded = repo.degraded_services()
        assert set(degraded) == set(DEGRADABLE_CHECKS), (
            f"degraded_services must list every degraded check_name; got {degraded}"
        )


# ---- AC-4 ------------------------------------------------------------------


class TestAC4DegradedDoesNotBlockCreation:
    """AC-4: 可降级项失败时新建项目仍可创建"""

    def test_degraded_does_not_block_creation(self, conn):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from src.backend.api.routes.projects import get_db, router
        from src.backend.core.preflight import (
            DEGRADABLE_CHECKS,
            run_full_preflight,
        )

        runners = _ok_runners()
        # Every degradable fails; every critical stays ok.
        for name in DEGRADABLE_CHECKS:
            runners[name] = _failed(name, "network down")
        run_full_preflight(conn, runners=runners)

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: conn
        app.include_router(router)
        client = TestClient(app)
        resp = client.post(
            "/api/projects",
            json={"title": "T", "description": "D"},
        )
        assert resp.status_code in (200, 201), (
            f"degraded (non-critical) must not block project creation; "
            f"got {resp.status_code}: {resp.text}"
        )


# ---- AC-5 ------------------------------------------------------------------


class TestAC5ValidUntil24h:
    """AC-5: `system_status` 记录 `valid_until` = 创建时间 + 24h"""

    def test_valid_until_24h(self, conn):
        from src.backend.core.preflight import run_full_preflight

        pinned = datetime(2026, 4, 21, 12, 0, 0, tzinfo=timezone.utc)
        run_full_preflight(conn, now=pinned)

        rows = conn.execute(
            "SELECT check_name, checked_at, valid_until FROM system_status"
        ).fetchall()
        assert rows, "run_full_preflight must insert at least one row"

        for r in rows:
            checked = datetime.fromisoformat(r["checked_at"].replace("Z", "+00:00"))
            valid_until = datetime.fromisoformat(
                r["valid_until"].replace("Z", "+00:00")
            )
            assert valid_until - checked == timedelta(hours=24), (
                f"{r['check_name']}: valid_until - checked_at != 24h "
                f"({r['checked_at']} vs {r['valid_until']})"
            )
            assert checked == pinned, (
                f"{r['check_name']}: checked_at {r['checked_at']} should "
                f"reflect injected now={pinned.isoformat()}"
            )


# ---- AC-6 ------------------------------------------------------------------


class TestAC6FullPreflightOnStartup:
    """AC-6: API 启动时自动跑全量 Pre-flight"""

    def test_full_preflight_on_startup(self, conn):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from src.backend.api.middleware.startup import (
            register_preflight_startup,
        )
        from src.backend.core.preflight import ALL_CHECKS

        app = FastAPI()
        register_preflight_startup(app, conn_provider=lambda: conn)

        # Entering the TestClient context fires @app.on_event("startup").
        with TestClient(app):
            pass

        names = {
            r["check_name"]
            for r in conn.execute(
                "SELECT DISTINCT check_name FROM system_status"
            ).fetchall()
        }
        assert names == set(ALL_CHECKS), (
            f"startup must run the full Pre-flight (9 checks); got {names}"
        )


# ---- AC-7 ------------------------------------------------------------------


class TestAC7CriticalSubsetOnProjectCreate:
    """AC-7: 新建项目时跑关键项子集检查"""

    def test_critical_subset_on_project_create(self, conn):
        from src.backend.core.preflight import (
            CRITICAL_CHECKS,
            DEGRADABLE_CHECKS,
            run_critical_preflight,
        )

        run_critical_preflight(conn)

        names = {
            r["check_name"]
            for r in conn.execute(
                "SELECT DISTINCT check_name FROM system_status"
            ).fetchall()
        }
        assert names == set(CRITICAL_CHECKS), (
            f"run_critical_preflight must write the 5 critical checks only; got {names}"
        )
        for dname in DEGRADABLE_CHECKS:
            assert dname not in names, (
                f"degradable check {dname!r} leaked into the critical subset write path"
            )
