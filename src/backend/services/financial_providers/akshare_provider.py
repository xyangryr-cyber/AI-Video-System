"""[SPEC-D-013] AkShare provider stub."""

from __future__ import annotations

from typing import Any

from src.backend.services.financial_providers.base_provider import BaseProvider


class AkShareProvider(BaseProvider):
    def fetch(self, *, symbol: str, start: str, end: str) -> dict[str, Any]:
        # AkShare covers Chinese symbols
        if any(symbol.startswith(p) for p in ("600", "000", "300", "688")):
            return {"status": "success", "data": [{"date": start, "close": 50.0}]}
        return {"status": "error", "reason": "symbol not in akshare scope"}
