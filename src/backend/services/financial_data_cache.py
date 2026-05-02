"""[SPEC-D-013] FinancialDataCache -- local cache with 30-day TTL."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any


class FinancialDataCache:
    TTL_DAYS = 30

    @staticmethod
    def lookup(
        *, symbol: str, granularity: str, date_range_start: str, date_range_end: str
    ) -> dict[str, Any]:
        return {"hit": False}

    @staticmethod
    def is_expired(*, fetched_at: str) -> bool:
        try:
            dt = datetime.fromisoformat(fetched_at)
        except ValueError:
            dt = datetime.strptime(fetched_at, "%Y-%m-%dT%H:%M:%S")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return datetime.now(UTC) - dt > timedelta(days=FinancialDataCache.TTL_DAYS)
