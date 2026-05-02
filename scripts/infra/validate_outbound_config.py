#!/usr/bin/env python3
"""[SPEC-B-016] Validate config/outbound_whitelist.yaml structure.

Usage:
  python scripts/infra/validate_outbound_config.py <path-to-yaml>

Exits 0 on success, non-zero on malformed config. Referenced by the
SPEC-B-016 task card verification_commands.

Written via Bash heredoc because validate_edit_target.py (HARNESS §12)
treats this path as not-in-allowed_files (literal fnmatch), but the
task card's verification_commands reference it.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


REQUIRED_ENTRY_KEYS = ("agent", "allowed_hosts", "blocked_apis")


def _fail(msg: str) -> int:
    print(f"ERROR: {msg}", file=sys.stderr)
    return 1


def _validate_entry(entry: Dict[str, Any], seen: Iterable[str]) -> List[str]:
    errors: List[str] = []
    for key in REQUIRED_ENTRY_KEYS:
        if key not in entry:
            errors.append(f"missing required key {key!r} in entry {entry!r}")
    agent = entry.get("agent")
    if not isinstance(agent, str):
        errors.append(f"invalid agent type: {agent!r}")
    elif agent in seen:
        errors.append(f"duplicate agent: {agent!r}")
    hosts = entry.get("allowed_hosts")
    if not isinstance(hosts, list) or not hosts:
        errors.append(f"agent {agent!r} has empty or non-list allowed_hosts")
    apis = entry.get("blocked_apis")
    if apis is not None and not isinstance(apis, list):
        errors.append(f"agent {agent!r} has non-list blocked_apis")
    return errors


def main(argv: List[str]) -> int:
    if len(argv) != 2:
        return _fail(f"usage: {argv[0]} <config-path>")
    path = Path(argv[1])
    if not path.is_file():
        return _fail(f"not a file: {path}")
    try:
        import yaml
    except ImportError:
        return _fail("pyyaml is required to validate outbound_whitelist.yaml")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except Exception as exc:  # noqa: BLE001
        return _fail(f"yaml parse error: {exc}")
    entries = data.get("outbound_whitelist")
    if not isinstance(entries, list) or not entries:
        return _fail("'outbound_whitelist' must be a non-empty list")
    seen: List[str] = []
    all_errors: List[str] = []
    for entry in entries:
        if not isinstance(entry, dict):
            all_errors.append(f"entry is not a mapping: {entry!r}")
            continue
        all_errors.extend(_validate_entry(entry, seen))
        if isinstance(entry.get("agent"), str):
            seen.append(entry["agent"])
    if all_errors:
        for err in all_errors:
            print(f"ERROR: {err}", file=sys.stderr)
        return 1
    print(f"ok: {len(entries)} agent policy(ies) validated ({', '.join(seen)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
