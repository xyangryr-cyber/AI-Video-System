"""[SPEC-D-013] YFinance provider stub."""

from __future__ import annotations

from typing import Any, Dict

from src.backend.services.financial_providers.base_provider import BaseProvider


class YFinanceProvider(BaseProvider):
    def fetch(self, *, symbol: str, start: str, end: str) -> Dict[str, Any]:
        if symbol in ("AAPL", "MSFT", "GOOGL"):
            return {"status": "success", "data": [{"date": start, "close": 150.0}]}
        return {"status": "error", "reason": "symbol not found"}
