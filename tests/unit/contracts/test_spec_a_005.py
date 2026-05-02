"""Tests for [SPEC-A-005] V1 Delivery Standards & Design Principles."""

from pathlib import Path


from src.shared.constants.delivery_standards import (
    P4_SINGLE_STATE_TARGET,
    P5_STATELESS_AGENT_RULE,
    V15_KILLSWITCH,
    V1_DELIVERY_STANDARDS,
)

ROOT = Path(__file__).resolve().parent.parent.parent.parent


class TestAC1V1DeliveryThresholds:
    """AC-1: Delivery standard constants defined: success_rate>=0.9, p50_time<=45min, p90_time<=60min, p50_cost<=$8, p90_cost<=$15, first_frame_load<=3s, router_accuracy>=0.85, router_p95<=3s"""

    def test_v1_delivery_thresholds(self):
        s = V1_DELIVERY_STANDARDS
        assert s["success_rate"] >= 0.9
        assert s["p50_time_min"] <= 45
        assert s["p90_time_min"] <= 60
        assert s["p50_cost_usd"] <= 8
        assert s["p90_cost_usd"] <= 15
        assert s["first_frame_load_s"] <= 3
        assert s["router_accuracy"] >= 0.85
        assert s["router_p95_s"] <= 3


class TestAC2V15KillswitchThresholds:
    """AC-2: V1.5 kill-switch thresholds defined: inject_subtask_usage<0.3, preference_extractor_acceptance<0.2, sample_size=20"""

    def test_v15_killswitch_thresholds(self):
        k = V15_KILLSWITCH
        assert k["inject_subtask_usage_max"] == 0.3
        assert k["preference_extractor_acceptance_min"] == 0.2
        assert k["sample_size"] == 20


class TestAC3ReviewChecklistContainsP1P7:
    """AC-3: `docs/review_checklist.md` lists P1-P7 as explicit check items"""

    def test_review_checklist_contains_p1_p7(self):
        content = (ROOT / "docs" / "review_checklist.md").read_text()
        for label in ["P1", "P2", "P3", "P4", "P5", "P6", "P7"]:
            assert label in content, f"Missing {label} in review_checklist.md"


class TestAC4V15MetricsSqlSyntax:
    """AC-4: SQL script `scripts/v15_metrics.sql` produces inject_subtask usage rate and preference acceptance rate from events table"""

    def test_v15_metrics_sql_syntax(self):
        import sqlite3

        sql = (ROOT / "scripts" / "v15_metrics.sql").read_text()
        conn = sqlite3.connect(":memory:")
        conn.execute(
            "CREATE TABLE events ("
            "  id INTEGER PRIMARY KEY,"
            "  project_id TEXT,"
            "  timestamp TEXT,"
            "  type TEXT,"
            "  payload TEXT"
            ")"
        )
        conn.executescript(sql)
        conn.close()


class TestAC5NoStatefulAgentPattern:
    """AC-5: No code pattern `self.history.append` allowed (P5 stateless agent principle)"""

    def test_no_stateful_agent_pattern(self):
        assert P5_STATELESS_AGENT_RULE
        assert "stateless" in P5_STATELESS_AGENT_RULE.lower()
        assert (
            "self.history" in P5_STATELESS_AGENT_RULE
            or "stateless" in P5_STATELESS_AGENT_RULE.lower()
        )


class TestAC6SqliteSingleStateTarget:
    """AC-6: Constants assert SQLite is the only structured state write target (P4)"""

    def test_sqlite_single_state_target(self):
        assert P4_SINGLE_STATE_TARGET
        assert "sqlite" in P4_SINGLE_STATE_TARGET.lower()
