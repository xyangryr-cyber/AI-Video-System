"""[RED] Tests for FinancialDataCacheRepository before implementation exists."""

import sqlite3

import pytest


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.execute(
        "CREATE TABLE IF NOT EXISTS financial_data_cache "
        "(symbol TEXT, provider TEXT, data_json TEXT, fetched_at REAL, "
        "PRIMARY KEY (symbol, provider))"
    )
    c.commit()
    return c


class TestFinancialDataCacheRepository:
    """RED: FinancialDataCacheRepository.delete_by_symbol_provider removes rows."""

    def test_delete_by_symbol_provider_removes_row(self, conn):
        from src.backend.db.repositories.financial_data_cache_repo import (
            FinancialDataCacheRepository,
        )

        conn.execute(
            "INSERT INTO financial_data_cache (symbol, provider, data_json, fetched_at) "
            "VALUES ('AAPL', 'yfinance', '{\"price\":100}', 1234567890.0)"
        )
        conn.commit()

        repo = FinancialDataCacheRepository(conn)
        repo.delete_by_symbol_provider("AAPL", "yfinance")

        row = conn.execute(
            "SELECT data_json FROM financial_data_cache "
            "WHERE symbol = 'AAPL' AND provider = 'yfinance'"
        ).fetchone()
        assert row is None

    def test_delete_by_symbol_provider_only_deletes_matching(self, conn):
        from src.backend.db.repositories.financial_data_cache_repo import (
            FinancialDataCacheRepository,
        )

        conn.execute(
            "INSERT INTO financial_data_cache (symbol, provider, data_json, fetched_at) "
            "VALUES ('AAPL', 'yfinance', '{\"price\":100}', 1234567890.0)"
        )
        conn.execute(
            "INSERT INTO financial_data_cache (symbol, provider, data_json, fetched_at) "
            "VALUES ('TSLA', 'yfinance', '{\"price\":200}', 1234567890.0)"
        )
        conn.commit()

        repo = FinancialDataCacheRepository(conn)
        repo.delete_by_symbol_provider("AAPL", "yfinance")

        remaining = conn.execute("SELECT symbol FROM financial_data_cache").fetchall()
        assert len(remaining) == 1
        assert remaining[0]["symbol"] == "TSLA"

    def test_upsert_cache_inserts_or_replaces(self, conn):
        from src.backend.db.repositories.financial_data_cache_repo import (
            FinancialDataCacheRepository,
        )

        repo = FinancialDataCacheRepository(conn)
        repo.upsert_cache("AAPL", "yfinance", '{"price":100}', 1234567890.0)

        row = conn.execute(
            "SELECT data_json FROM financial_data_cache "
            "WHERE symbol = 'AAPL' AND provider = 'yfinance'"
        ).fetchone()
        assert row is not None
        assert row["data_json"] == '{"price":100}'

        # Upsert again should replace
        repo.upsert_cache("AAPL", "yfinance", '{"price":150}', 9999999999.0)
        row2 = conn.execute(
            "SELECT data_json FROM financial_data_cache "
            "WHERE symbol = 'AAPL' AND provider = 'yfinance'"
        ).fetchone()
        assert row2["data_json"] == '{"price":150}'
