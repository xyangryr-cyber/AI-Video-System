"""[SMOKE-FIX-002] SQLite connection management.

Provides ``get_db_path()`` and ``create_connection()`` for the FastAPI
lifespan hook to wire the database dependency at startup.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path


def get_db_path() -> str:
    """Resolve the SQLite database path from env ``DATABASE_URL``.

    Default: ``data/db/dev.sqlite3`` (relative to project root).
    """
    db_raw = os.environ.get("DATABASE_URL", "sqlite:///data/db/dev.sqlite3")
    return db_raw.removeprefix("sqlite:///")


def create_connection(db_path: str | None = None) -> sqlite3.Connection:
    """Open a SQLite connection with ``check_same_thread=False`` and
    ``row_factory = sqlite3.Row``.

    Creates the parent directory if it does not exist.
    """
    if db_path is None:
        db_path = get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn
