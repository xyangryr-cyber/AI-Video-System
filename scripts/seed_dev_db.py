"""SPEC-B-018 AC-2: seed dev SQLite with 12 demo projects (one per phase 0..11).

Idempotent: deletes rows with `seed_tag='demo-2026-04-17'` before inserting.
The schema is the minimum needed for SPEC-E ProjectList rendering; once
SPEC-A-007 DDL is applied via Alembic, this script should switch to using
the real DDL instead of issuing CREATE TABLE itself.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

DEMO_TAG = "demo-2026-04-17"

DEMOS = [
    (i, f"demo-project-P{i}", "demo-category", i, "active", DEMO_TAG)
    for i in range(12)
]


def seed(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                current_phase INTEGER NOT NULL,
                status TEXT NOT NULL,
                seed_tag TEXT
            )
            """
        )
        con.execute("DELETE FROM projects WHERE seed_tag = ?", (DEMO_TAG,))
        con.executemany(
            "INSERT INTO projects (current_phase, project_id, title, category, status, seed_tag) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            [(phase, pid, title, cat, status, tag) for (phase, pid, title, cat, status, tag) in DEMOS],
        )
        con.commit()
    finally:
        con.close()


def main(argv: list[str]) -> int:
    db_path = Path(argv[0]) if argv else Path("data/db/dev.sqlite3")
    seed(db_path)
    print(f"seeded 12 demo projects into {db_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
