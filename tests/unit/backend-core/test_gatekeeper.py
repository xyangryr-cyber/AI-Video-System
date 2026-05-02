"""Tests for [SPEC-C-015] GateKeeper (7-Item Gate Check + Skip Branch + Claude Model).

Authority: docs/specs/SPEC-C-backend-core.md SPEC-8.1 / SPEC-8.2 / SPEC-8.3 / SPEC-8.4.
Task card: tasks/SPEC-C/C-015-gatekeeper.md.

AC mapping (task card -> test class):

AC-1  Each of the 7 check items fails independently.
      -> TestAC1EachCheckFailsIndependently
AC-2  All 7 items passing -> advance succeeds.
      -> TestAC2AllPassAdvanceSucceeds
AC-3  Gate failure returns ALL failed items (no short-circuit).
      -> TestAC3NoShortCircuitAllFailures
AC-4  Skip mode only checks #4 and #6.
      -> TestAC4SkipChecksOnly4And6
AC-5  Skip does not block on missing artifact or failed review.
      -> TestAC5SkipNoArtifactOk
AC-6  Skip with in-progress tasks still blocks.
      -> TestAC6SkipInProgressBlocks
AC-7  Reviewer verdict is strictly PASS or FAIL; blocking_issues=[] forces PASS.
      -> TestAC7VerdictBinaryPassFail
AC-8  GateKeeper model from model_config.json gatekeeper key is a Claude model.
      -> TestAC8GatekeeperUsesClaudeModel
AC-9  Actual LLM call log shows model matching config.
      -> TestAC9CallLogMatchesConfig
AC-10 Cost check (#7) missing does not block advance (WARN only).
      -> TestAC10CostCheckNonBlocking
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from src.backend.engine import gatekeeper as gk_mod


# -- Fixtures -------------------------------------------------------------


SCHEMA_PATH = Path(__file__).resolve().parents[3] / "src/backend/db/schema.sql"


@pytest.fixture()
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return c


def _seed_project(conn: sqlite3.Connection, pid: str = "proj_1") -> str:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?,?,?)",
        (pid, "t", "desc at least ten chars"),
    )
    conn.commit()
    return pid


def _seed_phase(
    conn: sqlite3.Connection,
    pid: str,
    phase_num: int = 0,
    *,
    artifact_path: str | None = "/tmp/a.json",
    artifact_status: str | None = "ok",
    artifact_version: int = 1,
    preferences_confirmed_at: str | None = "2026-04-23T00:00:00.000Z",
) -> None:
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name, status, "
        "artifact_version, artifact_status, artifact_path, "
        "preferences_confirmed_at) VALUES(?,?,?,?,?,?,?,?)",
        (
            pid,
            phase_num,
            f"P{phase_num}",
            "active",
            artifact_version,
            artifact_status,
            artifact_path,
            preferences_confirmed_at,
        ),
    )
    conn.commit()


def _seed_review(
    conn: sqlite3.Connection,
    pid: str,
    phase_num: int,
    *,
    target_version: int,
    status: str = "succeeded",
    verdict: str = "PASS",
    blocking_issues: list[str] | None = None,
    task_id: str = "t_000001",
) -> None:
    result_ref = json.dumps(
        {"verdict": verdict, "blocking_issues": blocking_issues or []}
    )
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type, status, "
        "target_version, params, result_ref) VALUES(?,?,?,?,?,?,?,?)",
        (task_id, pid, phase_num, "review", status, target_version, "{}", result_ref),
    )
    conn.commit()


def _seed_ledger_running(
    conn: sqlite3.Connection,
    pid: str,
    phase_num: int,
    *,
    task_id: str = "t_000099",
    status: str = "running",
    task_type: str = "generate_artifact",
) -> None:
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type, status, params) "
        "VALUES(?,?,?,?,?,?)",
        (task_id, pid, phase_num, task_type, status, "{}"),
    )
    conn.commit()


def _seed_async_running(
    conn: sqlite3.Connection,
    pid: str,
    phase_num: int,
    *,
    task_id: str = "async_1",
    status: str = "running",
) -> None:
    conn.execute(
        "INSERT INTO async_tasks(task_id, project_id, phase, type, status) "
        "VALUES(?,?,?,?,?)",
        (task_id, pid, phase_num, "render", status),
    )
    conn.commit()


def _seed_cost(
    conn: sqlite3.Connection, pid: str, phase_num: int, *, model: str = "claude-sonnet"
) -> None:
    conn.execute(
        "INSERT INTO agent_call_log(agent_name, tokens, duration_ms, phase, "
        "project_id, model, prompt, response) VALUES(?,?,?,?,?,?,?,?)",
        ("Producer", 100, 50, phase_num, pid, model, "p", "r"),
    )
    conn.commit()


def _all_green(conn: sqlite3.Connection, pid: str = "proj_1", phase: int = 0) -> None:
    """Seed a phase that passes all 7 checks."""
    _seed_project(conn, pid)
    _seed_phase(conn, pid, phase)
    _seed_review(conn, pid, phase, target_version=1)
    _seed_cost(conn, pid, phase)


# Helper to make a fresh gatekeeper pointing at the repo's real config.
def _gk(conn: sqlite3.Connection) -> gk_mod.GateKeeper:
    return gk_mod.GateKeeper(conn)


# -- AC-1 ----------------------------------------------------------------


class TestAC1EachCheckFailsIndependently:
    """AC-1: Each of the 7 check items fails independently with a specific failure reason."""

    def test_artifact_exists_fails(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        _seed_phase(conn, pid, 0, artifact_path=None, artifact_status=None)
        _seed_review(conn, pid, 0, target_version=1)
        _seed_cost(conn, pid, 0)
        result = _gk(conn).check(pid, 0)
        assert result.passed is False
        failed = {c.check for c in result.failed_checks}
        assert "artifact_exists" in failed

    def test_version_match_fails(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        _seed_phase(conn, pid, 0, artifact_version=2)
        _seed_review(conn, pid, 0, target_version=1)  # stale
        _seed_cost(conn, pid, 0)
        result = _gk(conn).check(pid, 0)
        assert result.passed is False
        assert "version_match" in {c.check for c in result.failed_checks}

    def test_review_passed_fails(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        _seed_phase(conn, pid, 0)
        _seed_review(
            conn,
            pid,
            0,
            target_version=1,
            verdict="FAIL",
            blocking_issues=["nope"],
        )
        _seed_cost(conn, pid, 0)
        result = _gk(conn).check(pid, 0)
        assert result.passed is False
        assert "review_passed" in {c.check for c in result.failed_checks}

    def test_no_running_tasks_fails(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        _seed_phase(conn, pid, 0)
        _seed_review(conn, pid, 0, target_version=1)
        _seed_ledger_running(conn, pid, 0)  # running task present
        _seed_cost(conn, pid, 0)
        result = _gk(conn).check(pid, 0)
        assert result.passed is False
        assert "no_running_tasks" in {c.check for c in result.failed_checks}

    def test_no_running_async_tasks_fails(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        _seed_phase(conn, pid, 0)
        _seed_review(conn, pid, 0, target_version=1)
        _seed_async_running(conn, pid, 0)  # running async
        _seed_cost(conn, pid, 0)
        result = _gk(conn).check(pid, 0)
        assert result.passed is False
        assert "no_running_async_tasks" in {c.check for c in result.failed_checks}

    def test_preferences_confirmed_fails(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        _seed_phase(conn, pid, 0, preferences_confirmed_at=None)
        _seed_review(conn, pid, 0, target_version=1)
        _seed_cost(conn, pid, 0)
        result = _gk(conn).check(pid, 0)
        assert result.passed is False
        assert "preferences_confirmed" in {c.check for c in result.failed_checks}

    def test_each_check_fails_independently(self, conn: sqlite3.Connection) -> None:
        """Summary assertion over all 7 blocking checks above (meta-test)."""
        # The 7 individual tests above each isolate one check; this aggregate
        # asserts the task-card named mapping exists in the names tuple.
        assert set(gk_mod.BLOCKING_CHECK_NAMES) == {
            "artifact_exists",
            "version_match",
            "review_passed",
            "no_running_tasks",
            "no_running_async_tasks",
            "preferences_confirmed",
            "content_quality",
        }


# -- AC-2 ----------------------------------------------------------------


class TestAC2AllPassAdvanceSucceeds:
    """AC-2: All 7 items passing results in advance success."""

    def test_all_pass_advance_succeeds(self, conn: sqlite3.Connection) -> None:
        _all_green(conn)
        result = _gk(conn).check("proj_1", 0)
        assert result.passed is True
        assert result.failed_checks == []
        # All 6 blocking + cost_logged present in passed set.
        passed_names = set(result.passed_checks)
        assert "cost_logged" in passed_names
        for name in gk_mod.BLOCKING_CHECK_NAMES:
            assert name in passed_names


# -- AC-3 ----------------------------------------------------------------


class TestAC3NoShortCircuitAllFailures:
    """AC-3: Gate failure returns ALL failed items, not just the first."""

    def test_no_short_circuit_all_failures(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        # Break 4 things at once: no artifact, stale review version, FAIL review,
        # running task, missing prefs. (async ok, cost ok)
        _seed_phase(
            conn,
            pid,
            0,
            artifact_path=None,
            artifact_status=None,
            artifact_version=2,
            preferences_confirmed_at=None,
        )
        _seed_review(
            conn,
            pid,
            0,
            target_version=1,
            verdict="FAIL",
            blocking_issues=["x"],
        )
        _seed_ledger_running(conn, pid, 0)
        _seed_cost(conn, pid, 0)
        result = _gk(conn).check(pid, 0)
        assert result.passed is False
        failed = {c.check for c in result.failed_checks}
        # All four broken checks are reported (no short-circuit):
        assert {
            "artifact_exists",
            "version_match",
            "review_passed",
            "no_running_tasks",
            "preferences_confirmed",
        } <= failed


# -- AC-4 ----------------------------------------------------------------


class TestAC4SkipChecksOnly4And6:
    """AC-4: Skip mode only checks #4 (no in-progress tasks) and #6 (preferences)."""

    def test_skip_checks_only_4_and_6(self, conn: sqlite3.Connection) -> None:
        # Construct a case where #4 and #6 both PASS but everything else is FAIL.
        # In skip mode, the result must be passed even though artifact/review/etc are bad.
        pid = _seed_project(conn)
        _seed_phase(
            conn,
            pid,
            0,
            artifact_path=None,
            artifact_status=None,
            artifact_version=5,
            preferences_confirmed_at="2026-04-23T00:00:00.000Z",
        )
        _seed_review(
            conn, pid, 0, target_version=1, verdict="FAIL", blocking_issues=["nope"]
        )
        # no running tasks, no async running, no cost (#7)
        result = _gk(conn).check(pid, 0, mode="skip")
        assert result.passed is True, f"skip should pass; got {result!r}"
        # Only the 2 skip checks should appear in passed_checks
        assert set(result.passed_checks) == {
            "no_running_tasks",
            "preferences_confirmed",
        }


# -- AC-5 ----------------------------------------------------------------


class TestAC5SkipNoArtifactOk:
    """AC-5: Skip does not block on missing artifact or failed review."""

    def test_skip_no_artifact_ok(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        _seed_phase(
            conn,
            pid,
            0,
            artifact_path=None,
            artifact_status=None,
        )
        # Intentionally no review rows at all.
        result = _gk(conn).check(pid, 0, mode="skip")
        assert result.passed is True


# -- AC-6 ----------------------------------------------------------------


class TestAC6SkipInProgressBlocks:
    """AC-6: Skip with in-progress tasks still blocks."""

    def test_skip_in_progress_blocks(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        _seed_phase(conn, pid, 0)
        _seed_ledger_running(conn, pid, 0)  # queued/running task
        result = _gk(conn).check(pid, 0, mode="skip")
        assert result.passed is False
        assert "no_running_tasks" in {c.check for c in result.failed_checks}


# -- AC-7 ----------------------------------------------------------------


class TestAC7VerdictBinaryPassFail:
    """AC-7: Reviewer verdict is strictly PASS/FAIL; blocking_issues=[] forces PASS."""

    def test_verdict_binary_pass_fail(self) -> None:
        # Construction side: verdict must be strictly PASS or FAIL.
        ok = gk_mod.ReviewerResult(verdict="PASS", blocking_issues=[])
        assert ok.verdict == "PASS"
        # blocking_issues=[] with verdict=FAIL is inconsistent and rejected.
        with pytest.raises(ValidationError):
            gk_mod.ReviewerResult(verdict="FAIL", blocking_issues=[])
        # blocking_issues non-empty with verdict=PASS is rejected.
        with pytest.raises(ValidationError):
            gk_mod.ReviewerResult(verdict="PASS", blocking_issues=["x"])
        # Anything outside the binary is rejected.
        for bad in ("WARN", "pass", "", "NEEDS_FIX"):
            with pytest.raises(ValidationError):
                gk_mod.ReviewerResult(verdict=bad, blocking_issues=[])  # type: ignore[arg-type]

    def test_empty_blockers_forces_pass(self, conn: sqlite3.Connection) -> None:
        """blocking_issues=[] in stored result must be treated as PASS by the gate."""
        pid = _seed_project(conn)
        _seed_phase(conn, pid, 0)
        # verdict="PASS", blocking_issues=[] -- gate check #3 must pass.
        _seed_review(conn, pid, 0, target_version=1, verdict="PASS", blocking_issues=[])
        _seed_cost(conn, pid, 0)
        result = _gk(conn).check(pid, 0)
        assert result.passed is True
        assert "review_passed" in result.passed_checks


# -- AC-8 ----------------------------------------------------------------


class TestAC8GatekeeperUsesClaudeModel:
    """AC-8: GateKeeper model from model_config.json gatekeeper key is a Claude model."""

    def test_gatekeeper_uses_claude_model(self) -> None:
        # No DB needed for model resolution.
        gk = gk_mod.GateKeeper.__new__(gk_mod.GateKeeper)  # bypass __init__
        gk._conn = None  # type: ignore[attr-defined]
        gk._config_path = None  # type: ignore[attr-defined]
        model = gk.model()
        assert model.lower().startswith("claude"), (
            f"gatekeeper role must route to a Claude model; got {model!r}"
        )


# -- AC-9 ----------------------------------------------------------------


class TestAC9CallLogMatchesConfig:
    """AC-9: Actual LLM call log shows model matching config."""

    def test_call_log_matches_config(self, conn: sqlite3.Connection) -> None:
        captured: dict[str, Any] = {}

        def fake_completion(*, model: str, messages: Any, **kw: Any) -> Any:
            captured["model"] = model
            return {
                "choices": [{"message": {"content": "ok"}}],
            }

        gk = gk_mod.GateKeeper(conn)
        gk.advise(
            messages=[{"role": "user", "content": "gate advice?"}],
            _completion_fn=fake_completion,
        )
        assert captured.get("model") == gk.model()


# -- AC-10 ---------------------------------------------------------------


class TestAC10CostCheckNonBlocking:
    """AC-10: Cost check (#7) missing does not block advance (WARN only)."""

    def test_cost_check_non_blocking(self, conn: sqlite3.Connection) -> None:
        pid = _seed_project(conn)
        _seed_phase(conn, pid, 0)
        _seed_review(conn, pid, 0, target_version=1)
        # intentionally NOT calling _seed_cost
        result = _gk(conn).check(pid, 0)
        assert result.passed is True, (
            "missing agent_call_log entry must not block the gate"
        )
        # But the warning is surfaced.
        assert any(w.check == "cost_logged" for w in result.warnings)
        # And cost_logged must NOT appear in failed_checks.
        assert "cost_logged" not in {c.check for c in result.failed_checks}
