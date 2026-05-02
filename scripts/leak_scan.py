#!/usr/bin/env python3
"""[SPEC-B-008] Daily leak scanner for agent_call_log.

Samples rows from agent_call_log and checks prompt/response fields for
un-redacted secrets via SECRET_REGEXES. Exit 1 when any hit is found.
"""
from __future__ import annotations

import argparse
import random
from typing import Any
import sqlite3
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO_ROOT))

from src.backend.core.redaction import SECRET_REGEXES  # noqa: E402
import re  # noqa: E402


def scan_lines(lines: list[str]) -> list[dict[str, Any]]:
    hits = []
    for i, line in enumerate(lines):
        for name, pattern in SECRET_REGEXES:
            if re.search(pattern, line):
                hits.append({"line": i, "rule": name, "match": line[:200]})
    return hits


def main() -> int:
    parser = argparse.ArgumentParser(description="Daily leak scan for agent_call_log")
    parser.add_argument("--db", default="data/db/app.sqlite3", help="SQLite DB path")
    parser.add_argument("--input", help="Text file to scan instead of DB")
    parser.add_argument("--sample-size", type=int, default=1000, help="Lines to sample")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be done")
    args = parser.parse_args()

    if args.dry_run:
        print(f"[DRY-RUN] Would scan {args.sample_size} lines from {args.input or args.db}")
        return 0

    lines: list[str] = []
    if args.input:
        content = Path(args.input).read_text(encoding="utf-8")
        lines = content.splitlines()
    else:
        db_path = Path(args.db)
        if not db_path.exists():
            print(f"DB not found: {db_path}", file=sys.stderr)
            return 0
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT prompt, response FROM agent_call_log "
            "ORDER BY RANDOM() LIMIT ?",
            (args.sample_size,),
        ).fetchall()
        for r in rows:
            lines.append(r["prompt"] or "")
            lines.append(r["response"] or "")
        conn.close()

    # Apply sample cap
    if len(lines) > args.sample_size:
        random.shuffle(lines)
        lines = lines[: args.sample_size]

    hits = scan_lines(lines)
    if hits:
        print(f"LEAK DETECTED: {len(hits)} hit(s)")
        for h in hits:
            print(f"  line {h['line']}: rule={h['rule']} match={h['match'][:100]}")
        return 1

    print(f"OK: scanned {len(lines)} lines, 0 leaks")
    return 0


if __name__ == "__main__":
    sys.exit(main())
