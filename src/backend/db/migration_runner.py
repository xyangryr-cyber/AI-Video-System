"""[SMOKE-FIX] Execute SQL migration files against a SQLite connection.

Reads ``*.sql`` files from a migrations directory in alphabetical order
and executes them. Uses ``CREATE TABLE IF NOT EXISTS`` semantics (already
in 001_initial.sql) for idempotency.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)


def run_migrations(conn: sqlite3.Connection, migrations_dir: str | Path) -> list[str]:
    """Execute all .sql files in *migrations_dir* in sorted order.

    Returns the list of applied file names.
    """
    directory = Path(migrations_dir)
    if not directory.is_dir():
        logger.warning("Migrations directory not found: %s", directory)
        return []

    applied: list[str] = []
    for sql_file in sorted(directory.glob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        conn.executescript(sql)
        conn.commit()
        applied.append(sql_file.name)
        logger.info("Applied migration: %s", sql_file.name)

    return applied
