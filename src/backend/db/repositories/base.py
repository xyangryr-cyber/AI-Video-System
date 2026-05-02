"""Repository base class -- the centralized hook for DB writes.

SPEC-B-002 AC-4 requires that all DB writes live in the repository
layer. Any module that needs to INSERT / UPDATE / DELETE rows in
SQLite MUST subclass ``BaseRepository`` and keep the SQL confined to
``src/backend/db/repositories/``.
"""

from __future__ import annotations

import sqlite3
from typing import Any


class BaseRepository:
    """Thin wrapper over a ``sqlite3.Connection`` for repositories."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def execute(self, sql: str, params: tuple[Any, ...] = ()) -> sqlite3.Cursor:
        return self._conn.execute(sql, params)

    def commit(self) -> None:
        self._conn.commit()
