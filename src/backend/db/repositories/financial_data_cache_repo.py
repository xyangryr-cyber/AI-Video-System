"""Repository for financial_data_cache table."""

from __future__ import annotations

from src.backend.db.repositories.base import BaseRepository


class FinancialDataCacheRepository(BaseRepository):
    def delete_by_symbol_provider(self, symbol: str, provider: str) -> None:
        self.execute(
            "DELETE FROM financial_data_cache WHERE symbol = ? AND provider = ?",
            (symbol, provider),
        )
        self.commit()

    def upsert_cache(
        self, symbol: str, provider: str, data_json: str, fetched_at: float
    ) -> None:
        self.execute(
            "INSERT OR REPLACE INTO financial_data_cache "
            "(symbol, provider, data_json, fetched_at) VALUES (?, ?, ?, ?)",
            (symbol, provider, data_json, fetched_at),
        )
        self.commit()
