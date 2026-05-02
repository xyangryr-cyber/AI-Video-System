#!/usr/bin/env python3
"""[SPEC-B-012] SQLite backup script -- creates a timestamped backup of the dev DB.

Usage:
    python3 scripts/backup_sqlite.py

Environment:
    DATABASE_URL -- SQLite connection URL (default: sqlite:///data/db/dev.sqlite3)
"""

from __future__ import annotations

import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path


def _get_db_path() -> Path:
    """Extract file path from DATABASE_URL environment variable."""
    db_url = os.environ.get("DATABASE_URL", "sqlite:///data/db/dev.sqlite3")
    if db_url.startswith("sqlite:///"):
        return Path(db_url[len("sqlite:///"):])
    return Path(db_url)


def _verify_backup(backup_path: Path) -> bool:
    """Open the backup and run SELECT 1 to verify it is valid."""
    try:
        conn = sqlite3.connect(str(backup_path), timeout=5)
        conn.execute("SELECT 1")
        conn.close()
        return True
    except sqlite3.Error as exc:
        print(f"Backup verification failed: {exc}", file=sys.stderr)
        return False


def main() -> None:
    db_path = _get_db_path()

    if not db_path.is_file():
        print(f"Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    # Create backups directory
    backup_dir = db_path.parent / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)

    # Generate timestamped backup filename
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    backup_name = f"dev.sqlite3.{ts}.bak"
    backup_path = backup_dir / backup_name

    # Copy the database file
    shutil.copy2(str(db_path), str(backup_path))
    print(f"Backup created: {backup_path}")

    # Verify the backup
    if _verify_backup(backup_path):
        print("Backup verified OK")
    else:
        print("Backup verification FAILED -- removing invalid backup", file=sys.stderr)
        backup_path.unlink(missing_ok=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
