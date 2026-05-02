"""[SPEC-D-013] Alpha Vantage provider stub."""

from __future__ import annotations

from typing import Any

from src.backend.services.financial_providers.base_provider import BaseProvider


class AlphaVantageProvider(BaseProvider):
    def fetch(self, *, symbol: str, start: str, end: str) -> dict[str, Any]:
        if symbol in ("AAPL", "MSFT", "GOOGL", "TSLA"):
            return {"status": "success", "data": [{"date": start, "close": 150.0}]}
        return {"status": "error", "reason": "symbol not found"}
