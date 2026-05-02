"""CRUD for ``system_status`` (SPEC-B-009).

The Pre-flight layer appends one row per check each time a preflight
sweep runs. Consumers want the *latest* row per ``check_name`` and we
aggregate from there into ``all_critical_ok`` / ``degraded_services``.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from src.backend.db.repositories.base import BaseRepository


class SystemStatusRepository(BaseRepository):
    def insert(
        self,
        check_name: str,
        status: str,
        message: str | None,
        checked_at: str,
        valid_until: str,
    ) -> None:
        self.execute(
            "INSERT INTO system_status "
            "(check_name, status, message, checked_at, valid_until) "
            "VALUES (?, ?, ?, ?, ?)",
            (check_name, status, message, checked_at, valid_until),
        )
        self.commit()

    def latest_all(self) -> list[sqlite3.Row]:
        """Latest row per ``check_name`` (by auto-increment ``id``)."""
        cur = self.execute(
            """
            SELECT s.*
            FROM system_status s
            JOIN (
                SELECT check_name, MAX(id) AS max_id
                FROM system_status
                GROUP BY check_name
            ) latest ON s.id = latest.max_id
            ORDER BY s.check_name
            """
        )
        return list(cur.fetchall())

    def all_critical_ok(self, critical_names: Iterable[str]) -> bool:
        """True iff every critical check_name has a latest row with
        ``status='ok'``. Missing checks count as not-ok (fail-closed).
        """
        by_name = {r["check_name"]: r for r in self.latest_all()}
        for name in critical_names:
            row = by_name.get(name)
            if row is None or row["status"] != "ok":
                return False
        return True

    def degraded_services(self) -> list[str]:
        """``check_name`` list for rows whose latest status is 'degraded'."""
        return [r["check_name"] for r in self.latest_all() if r["status"] == "degraded"]
