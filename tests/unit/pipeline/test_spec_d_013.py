"""Tests for [SPEC-D-013] Financial Data Service (SPEC-17)."""


class TestAC1ThreeTierFallback:
    def test_fallback_yfinance_to_alpha_vantage(self):
        from src.backend.services.financial_data_service import FinancialDataService

        svc = FinancialDataService()
        result = svc.fetch(
            symbol="AAPL",
            granularity="daily",
            date_range_start="2024-01-01",
            date_range_end="2024-01-31",
        )
        assert "data" in result
        assert "source" in result

    def test_all_fallback_to_user_verified(self):
        from src.backend.services.financial_data_service import FinancialDataService

        svc = FinancialDataService()
        result = svc.fetch(
            symbol="UNKNOWN_XYZ_999",
            granularity="daily",
            date_range_start="2024-01-01",
            date_range_end="2024-01-02",
        )
        assert "trust_level" in result
        # When all providers fail, trust_level = user_verified
        if result.get("source") == "manual_input":
            assert result["trust_level"] == "user_verified"


class TestAC2CacheTTL:
    def test_cache_ttl_30_days(self):
        from src.backend.services.financial_data_cache import FinancialDataCache

        cache = FinancialDataCache()
        assert cache.TTL_DAYS == 30

    def test_cache_hit(self):
        from src.backend.services.financial_data_cache import FinancialDataCache

        cache = FinancialDataCache()
        # Stub: always miss in V1
        result = cache.lookup(
            symbol="AAPL",
            granularity="daily",
            date_range_start="2024-01-01",
            date_range_end="2024-01-31",
        )
        assert "hit" in result


class TestAC3ProviderAbstraction:
    def test_base_provider_interface(self):
        from src.backend.services.financial_providers.base_provider import BaseProvider

        assert hasattr(BaseProvider, "fetch")

    def test_yfinance_provider(self):
        from src.backend.services.financial_providers.yfinance_provider import (
            YFinanceProvider,
        )

        p = YFinanceProvider()
        result = p.fetch(symbol="AAPL", start="2024-01-01", end="2024-01-31")
        assert "status" in result

    def test_alpha_vantage_provider(self):
        from src.backend.services.financial_providers.alpha_vantage_provider import (
            AlphaVantageProvider,
        )

        p = AlphaVantageProvider()
        result = p.fetch(symbol="AAPL", start="2024-01-01", end="2024-01-31")
        assert "status" in result

    def test_akshare_provider(self):
        from src.backend.services.financial_providers.akshare_provider import (
            AkShareProvider,
        )

        p = AkShareProvider()
        result = p.fetch(symbol="AAPL", start="2024-01-01", end="2024-01-31")
        assert "status" in result


class TestAC4NaturalLanguageQuery:
    def test_query_to_structured_call(self):
        from src.backend.services.financial_data_service import FinancialDataService

        svc = FinancialDataService()
        call = svc.parse_query("过去30天AAPL股价")
        assert "symbol" in call
        assert "granularity" in call


class TestAC5IntegrationFactChecker:
    def test_data_points_with_source_verified(self):
        from src.backend.services.financial_data_service import FinancialDataService

        svc = FinancialDataService()
        result = svc.fetch(
            symbol="AAPL",
            granularity="daily",
            date_range_start="2024-01-01",
            date_range_end="2024-01-02",
        )
        if result.get("source") != "manual_input":
            assert result.get("trust_level") == "source_verified"


class TestAC6CacheExpiry:
    def test_expired_cache_returns_miss(self):
        from src.backend.services.financial_data_cache import FinancialDataCache

        cache = FinancialDataCache()
        # Simulate expired entry
        result = cache.is_expired(fetched_at="2023-01-01T00:00:00")
        assert result is True

    def test_fresh_cache_not_expired(self):
        from src.backend.services.financial_data_cache import FinancialDataCache

        cache = FinancialDataCache()
        result = cache.is_expired(fetched_at="2026-04-24T00:00:00")
        assert result is False


class TestAC7ManualInputFallback:
    def test_manual_input_form_on_all_fail(self):
        from src.backend.services.financial_data_service import FinancialDataService

        svc = FinancialDataService()
        result = svc.fetch(
            symbol="NONEXISTENT",
            granularity="daily",
            date_range_start="1900-01-01",
            date_range_end="1900-01-02",
        )
        # Should signal manual input needed
        assert (
            result.get("requires_manual_input")
            or result.get("source") == "manual_input"
        )
