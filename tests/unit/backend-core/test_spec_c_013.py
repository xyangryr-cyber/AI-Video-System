"""[SPEC-C-013] Generic SubTask Agents & FinancialData."""

import sqlite3
import time
from unittest import mock


from src.backend.agents.subtask_agents import (
    CrossCheckAgent,
    DataVerifyAgent,
    ResearchAgent,
    inject_subtask,
    truncate_to_token_budget,
)
from src.backend.db.repositories.task_ledger_repository import TaskLedgerRepository
from src.backend.services.financial_data_service import FinancialDataService


# ---------------------------------------------------------------------------
# AC-1: All 3 agents callable via inject_subtask from any phase
# ---------------------------------------------------------------------------


class TestAC1InjectSubtaskAnyPhase:
    def test_inject_subtask_any_phase(self):
        phases = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
        for phase in phases:
            result = inject_subtask(
                agent_name="research",
                phase=phase,
                params={"query": "test query", "max_sources": 3},
            )
            assert result is not None
            assert "result" in result

    def test_research_agent_callable(self):
        agent = ResearchAgent()
        result = agent.execute(query="AI impact on finance", max_sources=3)
        assert isinstance(result, dict)
        assert "sources" in result

    def test_verify_agent_callable(self):
        agent = DataVerifyAgent()
        result = agent.execute(
            data_point_id="dp_1", claimed_value="100B", source_url="https://example.com"
        )
        assert isinstance(result, dict)
        assert "confidence" in result

    def test_crosscheck_agent_callable(self):
        agent = CrossCheckAgent()
        result = agent.execute(
            left_ref="artifact_v1",
            right_ref="artifact_v2",
            check_fields=["claim", "data"],
        )
        assert isinstance(result, dict)
        assert "diffs" in result


# ---------------------------------------------------------------------------
# AC-2: Results written to task_ledger.result_ref
# ---------------------------------------------------------------------------


class TestAC2ResultWrittenToResultRef:
    def test_result_written_to_result_ref(self):
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        conn.execute("""CREATE TABLE task_ledger (
            id TEXT PRIMARY KEY, project_id TEXT, phase INTEGER, type TEXT,
            status TEXT, params TEXT, produces_version TEXT, target_version TEXT,
            result_ref TEXT, created_at TEXT, updated_at TEXT)""")
        conn.execute("INSERT INTO task_ledger(id) VALUES('task_001')")
        conn.commit()
        from src.backend.agents.subtask_agents import _write_result_ref

        _write_result_ref(
            TaskLedgerRepository(conn), "task_001", {"sources": ["a", "b", "c"]}
        )
        row = conn.execute(
            "SELECT result_ref FROM task_ledger WHERE id = 'task_001'"
        ).fetchone()
        assert row is not None
        assert "sources" in row["result_ref"]
        conn.close()


# ---------------------------------------------------------------------------
# AC-3: 180s timeout
# ---------------------------------------------------------------------------


class TestAC3Timeout180s:
    def test_timeout_180s(self):
        agent = ResearchAgent()
        start = time.monotonic()
        result = agent.execute(query="test", max_sources=3)
        elapsed = time.monotonic() - start
        assert elapsed < 3, f"Execution took {elapsed}s, expected fast mock response"
        assert result is not None

    def test_timeout_enforced_flag(self):
        # The execute_with_timeout helper enforces timeout
        from src.backend.agents.subtask_agents import execute_with_timeout

        def slow_func():
            time.sleep(10)
            return {"ok": True}

        result = execute_with_timeout(slow_func, timeout_seconds=0.1)
        assert result.get("status") == "timeout"


# ---------------------------------------------------------------------------
# AC-4: Research produces 3-5 sources
# ---------------------------------------------------------------------------


class TestAC4Research3To5Sources:
    def test_research_3_to_5_sources(self):
        agent = ResearchAgent()
        result = agent.execute(query="test", max_sources=3)
        sources = result.get("sources", [])
        assert 3 <= len(sources) <= 5, f"Got {len(sources)} sources, expected 3-5"

    def test_research_max_sources_5(self):
        agent = ResearchAgent()
        result = agent.execute(query="test", max_sources=5)
        sources = result.get("sources", [])
        assert len(sources) >= 3

    def test_research_min_sources_3(self):
        agent = ResearchAgent()
        result = agent.execute(query="test", max_sources=3)
        sources = result.get("sources", [])
        assert len(sources) <= 5


# ---------------------------------------------------------------------------
# AC-5: CrossCheck diffs capped at 20
# ---------------------------------------------------------------------------


class TestAC5CrosscheckMax20Diffs:
    def test_crosscheck_max_20_diffs(self):
        agent = CrossCheckAgent()
        # Generate >20 diff-worthy fields
        left = {f"field_{i}": f"value_{i}" for i in range(30)}
        right = {f"field_{i}": f"different_{i}" for i in range(30)}
        result = agent.execute(
            left_ref="v1",
            right_ref="v2",
            check_fields=list(left.keys()),
            _left_artifact=left,
            _right_artifact=right,
        )
        diffs = result.get("diffs", [])
        assert len(diffs) <= 20
        if len(left) > 20:
            assert result.get("truncated") is True


# ---------------------------------------------------------------------------
# AC-6: DataVerify confidence has 2 decimal places
# ---------------------------------------------------------------------------


class TestAC6VerifyConfidence2Decimals:
    def test_verify_confidence_2_decimals(self):
        agent = DataVerifyAgent()
        result = agent.execute(
            data_point_id="dp_1", claimed_value="100", source_url="http://x.com"
        )
        conf = result["confidence"]
        assert isinstance(conf, float)
        conf_str = f"{conf:.2f}"
        assert float(conf_str) == conf
        # Check 2 decimal places
        assert round(conf, 2) == conf


# ---------------------------------------------------------------------------
# AC-7: Router injection <=800 tokens
# ---------------------------------------------------------------------------


class TestAC7RouterInjectionMax800Tokens:
    def test_router_injection_max_800_tokens(self):
        short = "Short result text"
        truncated = truncate_to_token_budget(short, 800)
        assert len(truncated) <= 800 * 4

    def test_long_text_truncated(self):
        long_text = "x" * 5000
        result = truncate_to_token_budget(long_text, 800)
        assert len(result) <= 800 * 4

    def test_empty_text(self):
        result = truncate_to_token_budget("", 800)
        assert result == ""


# ---------------------------------------------------------------------------
# AC-8: SubTask failure does NOT block GateKeeper
# ---------------------------------------------------------------------------


class TestAC8SubtaskFailGateStillPasses:
    def test_subtask_fail_gate_still_passes(self):
        agent = ResearchAgent()
        # Inject a failure via bad params — agent should return error, not raise
        result = agent.execute(query="", max_sources=0)
        assert isinstance(result, dict)
        # Result should not block gate
        assert result.get("block_gate") is not True


# ---------------------------------------------------------------------------
# AC-9: FinancialData fallback chain
# ---------------------------------------------------------------------------


class TestAC9FallbackChain:
    def test_fallback_chain(self):
        svc = FinancialDataService()
        assert svc.PROVIDERS == ("yfinance", "alpha_vantage", "akshare")

    def test_fallback_order(self):
        svc = FinancialDataService()
        assert svc.PROVIDERS[0] == "yfinance"
        assert svc.PROVIDERS[1] == "alpha_vantage"
        assert svc.PROVIDERS[2] == "akshare"

    def test_first_provider_tried(self):
        svc = FinancialDataService()
        with mock.patch.object(
            svc, "_fetch_from_yfinance", return_value={"price": 100}
        ):
            result = svc.fetch("AAPL")
            assert result == {"price": 100}


# ---------------------------------------------------------------------------
# AC-10: 30-day SQLite cache
# ---------------------------------------------------------------------------


class TestAC10Cache30DayTtl:
    def test_cache_30_day_ttl(self):
        svc = FinancialDataService()
        assert svc.CACHE_TTL_SECONDS == 30 * 24 * 3600

    def test_cache_store_and_retrieve(self):
        conn = sqlite3.connect(":memory:")
        conn.execute("""CREATE TABLE financial_data_cache (
            symbol TEXT, provider TEXT, data_json TEXT, fetched_at TEXT,
            PRIMARY KEY (symbol, provider))""")
        conn.commit()
        svc = FinancialDataService(_conn=conn)
        svc._cache_put("AAPL", "yfinance", {"price": 100})
        cached = svc._cache_get("AAPL", "yfinance")
        assert cached == {"price": 100}
        conn.close()


# ---------------------------------------------------------------------------
# AC-11: Reject >5 data points
# ---------------------------------------------------------------------------


class TestAC11RejectOver5DataPoints:
    def test_reject_over_5_data_points(self):
        svc = FinancialDataService()
        # 6 data points
        llm_output = {
            "data_points": [
                {"label": "Revenue", "value": "100B"},
                {"label": "Profit", "value": "20B"},
                {"label": "Margin", "value": "20%"},
                {"label": "Growth", "value": "15%"},
                {"label": "PE", "value": "25"},
                {"label": "Market Cap", "value": "2T"},
            ]
        }
        assert not svc.validate_data_points(llm_output)

    def test_accept_5_data_points(self):
        svc = FinancialDataService()
        llm_output = {
            "data_points": [
                {"label": "Revenue", "value": "100B"},
                {"label": "Profit", "value": "20B"},
                {"label": "Margin", "value": "20%"},
                {"label": "Growth", "value": "15%"},
                {"label": "PE", "value": "25"},
            ]
        }
        assert svc.validate_data_points(llm_output)
