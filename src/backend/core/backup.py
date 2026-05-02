"""SQLite backup helper (SPEC-B-006 / SPEC-12.3).

The sole recovery source is ``app.sqlite3.bak`` next to the live DB.
Restoring from export views (``snapshot.md``, ``project_state.json``)
is explicitly forbidden -- those are read-only projections. See
SPEC-12.3 AC-2.

Uses ``sqlite3.Connection.backup`` so the copy is consistent even if
writers are touching the source at the same time (unlike ``shutil.copy``
on a hot DB file).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

BACKUP_SUFFIX = ".bak"


def backup_path_for(db_path: Path) -> Path:
    """Canonical backup location: ``<db_path>.bak``.

    For the production DB ``data/db/app.sqlite3`` this resolves to
    ``data/db/app.sqlite3.bak``. The recovery runbook loads this file
    and this file only.
    """
    return db_path.with_name(db_path.name + BACKUP_SUFFIX)


def create_sqlite_backup(db_path: Path) -> Path:
    """Make a consistent copy of ``db_path`` at ``<db_path>.bak``.

    Returns the backup path. Raises ``FileNotFoundError`` if the
    source DB does not exist. Uses SQLite's online ``.backup()``
    API (not a raw file copy) so the output is always transactionally
    consistent.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise FileNotFoundError(f"source DB not found: {db_path}")
    dst = backup_path_for(db_path)
    src_conn = sqlite3.connect(str(db_path))
    try:
        dst_conn = sqlite3.connect(str(dst))
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()
    return dst
