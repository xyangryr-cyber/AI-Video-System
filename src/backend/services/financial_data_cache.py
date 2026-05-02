"""[SPEC-D-013] FinancialDataCache -- local cache with 30-day TTL."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict


class FinancialDataCache:
    TTL_DAYS = 30

    @staticmethod
    def lookup(
        *, symbol: str, granularity: str, date_range_start: str, date_range_end: str
    ) -> Dict[str, Any]:
        return {"hit": False}

    @staticmethod
    def is_expired(*, fetched_at: str) -> bool:
        try:
            dt = datetime.fromisoformat(fetched_at)
        except ValueError:
            dt = datetime.strptime(fetched_at, "%Y-%m-%dT%H:%M:%S")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) - dt > timedelta(
            days=FinancialDataCache.TTL_DAYS
        )
