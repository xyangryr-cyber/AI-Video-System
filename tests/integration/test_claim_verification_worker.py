"""[SPEC-B-100] claim_verification 队列 + 告警 + Dashboard 指标 — integration tests.

Authority:
- SPEC-B §B-BDD-1.1 (v3.16): retry_delays_sec [30,120,600], max_attempts 3,
  dead_letter_handler writes verification_records.verdict='inconclusive'.
- SPEC-B §B-BDD-1.2: alert thresholds — task card narrows SPEC default to
  pending > 100 OR dead_letter > 5 (task card is authoritative scope).
- SPEC-B §B-BDD-1.3: Dashboard — task card narrows SPEC default to exactly
  four metrics: pending_count, verifying_latency_p95, failed_rate,
  hard_blocking_count.

Allowed-files-compliant module; ``tests/unit/infra/test_spec_b_100.py``
delegates via class-inheritance (B-015/B-016 precedent).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]


# --------------------------------------------------------------------------- #
# AC-1: 指数退避 30s -> 2m -> 10m; 3 次失败入死信队列
# --------------------------------------------------------------------------- #


class TestAC1ExponentialBackoffAndDeadLetter:
    """AC-1: retry delays [30, 120, 600]; after 3 failures route to dead letter."""

    def test_exponential_backoff_and_dead_letter(self):
        from src.backend.workers.claim_verification_worker import (
            DEAD_LETTER_VERDICT,
            MAX_ATTEMPTS,
            RETRY_DELAYS_SEC,
            handle_failure,
        )

        # Retry ladder is exactly [30, 120, 600] seconds.
        assert tuple(RETRY_DELAYS_SEC) == (30, 120, 600), (
            f"expected (30,120,600), got {tuple(RETRY_DELAYS_SEC)!r}"
        )
        assert MAX_ATTEMPTS == 3
        assert DEAD_LETTER_VERDICT == "inconclusive"

        # Attempts 1 and 2 return retry with the spec-mandated delays.
        r1 = handle_failure(attempt=1)
        assert r1["action"] == "retry" and r1["delay_sec"] == 30
        r2 = handle_failure(attempt=2)
        assert r2["action"] == "retry" and r2["delay_sec"] == 120
        # Attempt 3 is the final failure -> dead letter, verdict=inconclusive.
        r3 = handle_failure(attempt=3)
        assert r3["action"] == "dead_letter"
        assert r3["verdict"] == "inconclusive"


# --------------------------------------------------------------------------- #
# AC-2: Dashboard 输出 4 个指标
# --------------------------------------------------------------------------- #


def _seed_test_db(conn: sqlite3.Connection) -> None:
    """Create the minimal schema the metrics collector reads from."""
    conn.executescript(
        """
        CREATE TABLE claims (
            claim_id TEXT PRIMARY KEY,
            claim_type TEXT NOT NULL,
            text TEXT NOT NULL,
            source_phase TEXT NOT NULL,
            source_artifact TEXT NOT NULL,
            blocking_level TEXT NOT NULL DEFAULT 'none',
            verification_status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        );
        CREATE TABLE async_tasks (
            task_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL,
            phase INTEGER NOT NULL,
            type TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            attempt INTEGER NOT NULL DEFAULT 1,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            started_at TEXT,
            finished_at TEXT,
            error TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE projects (project_id TEXT PRIMARY KEY);
        INSERT INTO projects(project_id) VALUES ('proj_x');
        """
    )


class TestAC2DashboardEmitsFourMetrics:
    """AC-2: Dashboard emits exactly four metric keys."""

    def test_dashboard_emits_four_metrics(self, tmp_path):
        from scripts.dashboard_metrics import collect_metrics

        conn = sqlite3.connect(":memory:")
        _seed_test_db(conn)
        # seed 2 pending claim_verification tasks, 1 succeeded, 1 failed,
        # plus one hard-blocking claim.
        conn.executemany(
            "INSERT INTO async_tasks"
            "(task_id, project_id, phase, type, status, attempt, max_attempts,"
            " started_at, finished_at, created_at) VALUES "
            "(?,?,?,?,?,?,?,?,?,?)",
            [
                (
                    "t1",
                    "proj_x",
                    2,
                    "claim_verification",
                    "pending",
                    1,
                    3,
                    None,
                    None,
                    "2026-04-22T00:00:00.000Z",
                ),
                (
                    "t2",
                    "proj_x",
                    2,
                    "claim_verification",
                    "queued",
                    1,
                    3,
                    None,
                    None,
                    "2026-04-22T00:00:00.000Z",
                ),
                (
                    "t3",
                    "proj_x",
                    2,
                    "claim_verification",
                    "succeeded",
                    1,
                    3,
                    "2026-04-22T00:00:00.000Z",
                    "2026-04-22T00:00:05.000Z",
                    "2026-04-22T00:00:00.000Z",
                ),
                (
                    "t4",
                    "proj_x",
                    2,
                    "claim_verification",
                    "failed",
                    3,
                    3,
                    "2026-04-22T00:00:00.000Z",
                    "2026-04-22T00:00:02.000Z",
                    "2026-04-22T00:00:00.000Z",
                ),
            ],
        )
        conn.execute(
            "INSERT INTO claims(claim_id, claim_type, text, source_phase,"
            " source_artifact, blocking_level, verification_status,"
            " created_at) VALUES"
            " ('c1','fact','t','P2','a','hard','pending',"
            "  '2026-04-22T00:00:00.000Z')"
        )
        conn.commit()

        metrics = collect_metrics(conn)

        assert set(metrics.keys()) == {
            "pending_count",
            "verifying_latency_p95",
            "failed_rate",
            "hard_blocking_count",
        }, f"unexpected metric keys: {sorted(metrics)}"
        # Spot-check values.
        assert metrics["pending_count"] == 2
        assert metrics["hard_blocking_count"] == 1
        # 1 failed out of 2 terminal (succeeded+failed) = 0.5
        assert abs(metrics["failed_rate"] - 0.5) < 1e-6
        # p95 with a single 5-second latency sample -> 5.
        assert metrics["verifying_latency_p95"] == pytest.approx(5.0, abs=0.01)


# --------------------------------------------------------------------------- #
# AC-3: 告警触发条件 pending>100 OR dead_letter>5
# --------------------------------------------------------------------------- #


class TestAC3AlertThresholds:
    """AC-3: pending > 100 or dead_letter > 5 fires alert."""

    def _load_alerts(self):
        yaml = pytest.importorskip("yaml")
        path = PROJECT_ROOT / "config" / "alerts" / "claim_verification.yaml"
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    def test_alert_config_has_two_rules(self):
        alerts = self._load_alerts()
        rules = alerts.get("alerts") or []
        names = {r.get("name") for r in rules if isinstance(r, dict)}
        assert "claim_verification_pending_over_100" in names
        assert "claim_verification_dead_letter_over_5" in names

    def test_alert_triggers_on_pending_and_dead_letter_thresholds(self):
        from scripts.dashboard_metrics import check_alerts

        alerts = self._load_alerts()

        # Below thresholds -> no alerts.
        fired = check_alerts(
            {"pending_count": 100, "dead_letter_count": 5},
            alerts_config=alerts,
        )
        assert fired == [], f"did not expect alerts, got {fired!r}"

        # pending > 100 -> fires pending alert.
        fired_p = check_alerts(
            {"pending_count": 101, "dead_letter_count": 0},
            alerts_config=alerts,
        )
        assert any(
            a["name"] == "claim_verification_pending_over_100" for a in fired_p
        ), f"expected pending alert, got {fired_p!r}"

        # dead_letter > 5 -> fires dead_letter alert.
        fired_d = check_alerts(
            {"pending_count": 0, "dead_letter_count": 6},
            alerts_config=alerts,
        )
        assert any(
            a["name"] == "claim_verification_dead_letter_over_5" for a in fired_d
        ), f"expected dead_letter alert, got {fired_d!r}"


# --------------------------------------------------------------------------- #
# AC-4: 高优先级 challenge_claim 队列 延迟 p95 < 30s
# --------------------------------------------------------------------------- #


class TestAC4ChallengeClaimPriorityLatency:
    """AC-4: priority worker enforces p95 latency budget < 30s."""

    def test_priority_queue_config(self):
        from src.backend.workers.claim_verification_priority_worker import (
            PRIORITY_LATENCY_BUDGET_P95_SEC,
            QUEUE_NAME,
            QUEUE_PRIORITY,
        )

        assert QUEUE_NAME == "claim_verification_priority"
        assert QUEUE_PRIORITY == "high"
        assert PRIORITY_LATENCY_BUDGET_P95_SEC == 30

    def test_challenge_claim_priority_queue_latency_under_30s(self):
        from src.backend.workers.claim_verification_priority_worker import (
            compute_p95_latency,
            is_priority_latency_within_budget,
        )

        # 100 synthetic latency samples all under 30s -> p95 within budget.
        good = [float(i % 25) + 1.0 for i in range(100)]
        p95 = compute_p95_latency(good)
        assert p95 < 30, f"p95 should be < 30, got {p95}"
        assert is_priority_latency_within_budget(good) is True

        # A single over-budget sample blows p95 past 30s for a tight set.
        bad = [1.0] * 94 + [35.0] * 6
        assert is_priority_latency_within_budget(bad) is False
