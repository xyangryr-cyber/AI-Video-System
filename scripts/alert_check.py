#!/usr/bin/env python3
"""[SPEC-B-010] Standalone alert checker for cron/Dashboard use.

Connects to the SQLite DB, runs all alert checks, and emits JSON
to stdout. Exit 1 iff any alert fires.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.backend.core.alerts import check_alerts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Alert checker")
    parser.add_argument("--db", default="data/db/app.sqlite3", help="SQLite DB path")
    parser.add_argument("--json", action="store_true", default=True, help="JSON output")
    args = parser.parse_args()

    db_path = Path(args.db)
    if not db_path.exists():
        print(json.dumps({"error": f"DB not found: {db_path}"}))
        return 2

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    results = check_alerts(conn)
    conn.close()

    output = {
        "alerts": results,
        "fired": [a for a in results if a.get("fired")],
        "ok": [a for a in results if not a.get("fired")],
    }
    print(json.dumps(output, indent=2, default=str))

    return 1 if output["fired"] else 0


if __name__ == "__main__":
    sys.exit(main())
