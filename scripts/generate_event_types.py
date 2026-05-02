#!/usr/bin/env python3
"""[GAPFIX-030] Cross-language event type consistency checker.

Verifies that the 17 WebSocket event types are consistent across:
  - src/shared/contracts/event_types.py
  - src/shared/contracts/event_types.ts
  - src/shared/constants/event_types.py   (stretch)
  - src/shared/constants/event_types.ts   (stretch)

Usage:
  python3 scripts/generate_event_types.py --check    # exit 0 if consistent, 1 if not
  python3 scripts/generate_event_types.py             # full report
  python3 scripts/generate_event_types.py --help
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from typing import Dict, List, Set, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CONTRACT_PY = os.path.join(PROJECT_ROOT, "src", "shared", "contracts", "event_types.py")
CONTRACT_TS = os.path.join(PROJECT_ROOT, "src", "shared", "contracts", "event_types.ts")
CONSTANTS_PY = os.path.join(PROJECT_ROOT, "src", "shared", "constants", "event_types.py")
CONSTANTS_TS = os.path.join(PROJECT_ROOT, "src", "shared", "constants", "event_types.ts")

EXPECTED_COUNT = 17


# ---------------------------------------------------------------------------
# extractors
# ---------------------------------------------------------------------------

def _extract_py_event_values(path: str) -> Set[str]:
    """Extract event type string values from a Python Enum file."""
    if not os.path.isfile(path):
        return set()
    values: Set[str] = set()
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(r'^\s+\w+\s*=\s*"([^"]+)"', content, re.MULTILINE):
        values.add(m.group(1))
    return values


def _extract_ts_event_values(path: str) -> Set[str]:
    """Extract event type string values from a TypeScript const file."""
    if not os.path.isfile(path):
        return set()
    values: Set[str] = set()
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    for m in re.finditer(r':\s*"([^"]+)"', content):
        values.add(m.group(1))
    if not values:
        for m in re.finditer(r'"([^"]+)"', content):
            values.add(m.group(1))
    return values


# ---------------------------------------------------------------------------
# check logic
# ---------------------------------------------------------------------------

def _check_file_pair(name: str, py_path: str, ts_path: str) -> Tuple[bool, str]:
    py_vals = _extract_py_event_values(py_path)
    ts_vals = _extract_ts_event_values(ts_path)

    if not py_vals and not ts_vals:
        return False, f"{name}: both files empty or unreadable"

    only_py = py_vals - ts_vals
    only_ts = ts_vals - py_vals
    common = py_vals & ts_vals

    issues: List[str] = []
    if only_py:
        issues.append(f"Python-only: {sorted(only_py)}")
    if only_ts:
        issues.append(f"TypeScript-only: {sorted(only_ts)}")
    if len(common) != EXPECTED_COUNT:
        issues.append(f"count={len(common)}, expected={EXPECTED_COUNT}")

    if issues:
        return False, f"{name}: MISMATCH — {'; '.join(issues)}"
    return True, f"{name}: OK — {len(common)}/{EXPECTED_COUNT} events consistent"


def run_check(stretch: bool = False) -> Tuple[bool, List[str]]:
    results: List[str] = []
    all_ok = True

    ok, msg = _check_file_pair("contracts/event_types", CONTRACT_PY, CONTRACT_TS)
    results.append(msg)
    if not ok:
        all_ok = False

    if stretch:
        ok, msg = _check_file_pair("constants/event_types", CONSTANTS_PY, CONSTANTS_TS)
        results.append(msg)
        if not ok:
            all_ok = False

        contract_py = _extract_py_event_values(CONTRACT_PY)
        constants_py = _extract_py_event_values(CONSTANTS_PY)
        contract_ts = _extract_ts_event_values(CONTRACT_TS)
        constants_ts = _extract_ts_event_values(CONSTANTS_TS)

        py_diff = contract_py.symmetric_difference(constants_py)
        ts_diff = contract_ts.symmetric_difference(constants_ts)
        if py_diff:
            results.append(f"contracts vs constants py diff: {sorted(py_diff)}")
            all_ok = False
        else:
            results.append("contracts vs constants py: IDENTICAL")
        if ts_diff:
            results.append(f"contracts vs constants ts diff: {sorted(ts_diff)}")
            all_ok = False
        else:
            results.append("contracts vs constants ts: IDENTICAL")

    return all_ok, results


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Cross-language event type consistency checker."
    )
    parser.add_argument(
        "--check", action="store_true",
        help="Exit 0 if consistent, 1 if gaps found"
    )
    parser.add_argument(
        "--stretch", action="store_true",
        help="Also verify src/shared/constants/ event_types"
    )
    args = parser.parse_args()

    all_ok, results = run_check(stretch=args.stretch)

    for r in results:
        prefix = "PASS" if "OK" in r or "IDENTICAL" in r else "FAIL"
        print(f"{prefix}: {r}")

    if args.check:
        return 0 if all_ok else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
