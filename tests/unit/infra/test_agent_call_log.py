"""Tests for [SPEC-B-007] agent_call_log table and cost aggregation.

Real assertions for AC-1..AC-5 covering auto-logging, token/duration
validation, cost aggregation, $15 WARN threshold, and no-circuit-breaker.

Coverage:
* AC-1: Every LLM call auto-writes one row into agent_call_log.
* AC-2: tokens > 0, duration_ms is measured (not a constant).
* AC-3: Per-phase cost sums equal total_cost_usd.
* AC-4: Single-project LLM cost > $15 emits WARN log.
* AC-5: V1 has no circuit-breaker logic (search confirms zero hits).
"""

from __future__ import annotations

import logging
import sqlite3
import time
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
        (pid, "Test Project", "test"),
    )


# --- AC-1: auto-log on LLM call ----------------------------------------------


class TestAC1AutoLogOnLlmCall:
    def test_auto_log_on_llm_call(self, conn: sqlite3.Connection):
        """Call llm_client and assert one fresh row in agent_call_log."""
        _insert_project(conn)
        from src.backend.core.llm_client import LLMClient

        def fake_completion(**kwargs):
            return {
                "choices": [{"message": {"content": '{"ok": true}'}}],
                "usage": {
                    "total_tokens": 150,
                    "prompt_tokens": 50,
                    "completion_tokens": 100,
                },
                "model": kwargs.get("model", "test-model"),
            }

        client = LLMClient(conn)
        before = conn.execute("SELECT COUNT(*) AS n FROM agent_call_log").fetchone()[
            "n"
        ]

        client.chat_completion(
            role="producer",
            messages=[{"role": "user", "content": "hello"}],
            agent_name="TestAgent",
            phase=3,
            project_id="proj_a",
            _completion_fn=fake_completion,
        )

        after = conn.execute("SELECT COUNT(*) AS n FROM agent_call_log").fetchone()["n"]
        assert after == before + 1

        row = conn.execute(
            "SELECT * FROM agent_call_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert row["agent_name"] == "TestAgent"
        assert row["phase"] == 3
        assert row["project_id"] == "proj_a"
        assert row["model"] == "test-model"
        assert "hello" in row["prompt"]


# --- AC-2: tokens positive, duration measured --------------------------------


class TestAC2TokensPositiveDurationMeasured:
    def test_tokens_positive_duration_measured(self, conn: sqlite3.Connection):
        """tokens > 0 and duration_ms is a real measurement (not hardcoded)."""
        _insert_project(conn)
        from src.backend.core.llm_client import LLMClient

        fake_durations = [0.05, 0.10]
        call_count = [0]

        def fake_completion(**kwargs):
            idx = min(call_count[0], len(fake_durations) - 1)
            time.sleep(fake_durations[idx])
            call_count[0] += 1
            return {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"total_tokens": 200},
                "model": "m",
            }

        client = LLMClient(conn)
        durations = []
        for i in range(2):
            client.chat_completion(
                role="producer",
                messages=[{"role": "user", "content": "msg"}],
                agent_name="Agent",
                phase=1,
                project_id="proj_a",
                _completion_fn=fake_completion,
            )
            row = conn.execute(
                "SELECT tokens, duration_ms FROM agent_call_log ORDER BY id DESC LIMIT 1"
            ).fetchone()
            assert row["tokens"] > 0
            assert row["duration_ms"] >= 40  # 0.05s * 1000 = 50ms min
            durations.append(row["duration_ms"])

        assert len(set(durations)) > 1, (
            f"durations should differ across calls, got {durations}"
        )


# --- AC-3: by-phase sum equals total -----------------------------------------


class TestAC3ByPhaseSumEqualsTotal:
    def test_by_phase_sum_equals_total(self, conn: sqlite3.Connection):
        """Per-phase aggregated cost equals total_cost_usd."""
        _insert_project(conn)
        from src.backend.core.llm_client import LLMClient
        from src.backend.core.cost_aggregator import CostAggregator

        def fake_completion(**kwargs):
            return {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"total_tokens": 1000},
                "model": "m",
            }

        client = LLMClient(conn)
        # Call phase 1 twice, phase 2 once
        for ph in (1, 1, 2):
            client.chat_completion(
                role="producer",
                messages=[{"role": "user", "content": "msg"}],
                agent_name="A",
                phase=ph,
                project_id="proj_a",
                _completion_fn=fake_completion,
            )

        agg = CostAggregator(conn)
        total = agg.total_cost_usd("proj_a")
        by_phase = agg.by_phase("proj_a")

        assert total > 0
        phase_sum = sum(by_phase.values())
        assert phase_sum == pytest.approx(total, rel=1e-9)


# --- AC-4: cost warn at $15 --------------------------------------------------


class TestAC4CostWarnAt15Dollars:
    def test_cost_warn_at_15_dollars(self, conn: sqlite3.Connection, caplog):
        """WARN log emitted when single-project cost exceeds $15."""
        _insert_project(conn)
        from src.backend.core.llm_client import LLMClient

        def fake_completion(**kwargs):
            return {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"total_tokens": 8_000_000},
                "model": "m",
            }

        client = LLMClient(conn)
        with caplog.at_level(logging.WARNING):
            client.chat_completion(
                role="producer",
                messages=[{"role": "user", "content": "msg"}],
                agent_name="A",
                phase=1,
                project_id="proj_a",
                _completion_fn=fake_completion,
            )

        warn_records = [r for r in caplog.records if r.levelno >= logging.WARNING]
        cost_warns = [
            r for r in warn_records if "cost" in r.message.lower() or "15" in r.message
        ]
        assert len(cost_warns) >= 1, (
            f"Expected cost WARN when project exceeds $15, got {warn_records}"
        )


# --- AC-5: no circuit breaker in V1 ------------------------------------------


class TestAC5NoCircuitBreakerV1:
    def test_no_circuit_breaker_v1(self):
        """Search backend source for circuit-break/fuse/熔断 — must have zero hits."""
        import subprocess

        result = subprocess.run(
            ["grep", "-rnI", "circuit_break\\|熔断", "src/backend/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        # grep exits 1 when no matches (which is the desired outcome)
        hit_lines = [
            line
            for line in result.stdout.splitlines()
            if not line.strip().startswith("#") and not line.strip().startswith("//")
        ]
        assert len(hit_lines) == 0, f"Circuit breaker found: {hit_lines}"
