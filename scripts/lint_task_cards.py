#!/usr/bin/env python3
"""Lint task cards under tasks/SPEC-*/ for Loop readiness.

Checks per card:
  1. STRUCT    - has 'Verification Commands' section
  2. RUNNABLE  - section contains >= 1 pytest/vitest/npx command
  3. PATH_OK   - every test-file path in verification commands exists on disk
  4. CANON_OK  - canonical tests/unit/<layer>/test_spec_<x>_<nnn>.py exists for this task
  5. MAP_OK    - every test file in 'Test Mapping' appears in verification commands

Exit code 0 = all pass, 1 = any finding.
Usage: python scripts/lint_task_cards.py [--json] [--only SPEC-D]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"
TESTS = ROOT / "tests"

LAYER_MAP = {
    "A": "contracts",
    "B": "infra",
    "C": "backend-core",
    "D": "pipeline",
    "E": "frontend",
    "F": "media-render",
    "G": "workers",
}

TASK_ID_RE = re.compile(r"SPEC-([A-G])-(\d+)")
PYTEST_PATH_RE = re.compile(r"(?:pytest|vitest(?:\s+run)?)\s+(\S+\.(?:py|tsx?|ts))")
TEST_PATH_RE = re.compile(r"(tests/[\w/.\-]+\.(?:py|tsx?|ts))")


def find_section(text: str, header: str) -> str:
    pattern = rf"(?m)^##\s+{re.escape(header)}\s*\n(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else ""


def extract_pytest_files(verif: str) -> list[str]:
    return PYTEST_PATH_RE.findall(verif)


def extract_mapping_files(mapping: str) -> list[str]:
    return list(set(TEST_PATH_RE.findall(mapping)))


def canonical_test(layer: str, nnn: str) -> Path:
    sub = LAYER_MAP.get(layer.upper(), "unknown")
    return TESTS / "unit" / sub / f"test_spec_{layer.lower()}_{nnn.zfill(3)}.py"


def lint_card(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    rel = path.relative_to(ROOT).as_posix()

    m = TASK_ID_RE.search(text)
    task_id = f"SPEC-{m.group(1)}-{m.group(2)}" if m else path.stem
    layer = m.group(1) if m else "?"
    nnn = m.group(2) if m else "?"

    findings: list[str] = []

    verif = find_section(text, "Verification Commands")
    if not verif:
        findings.append("STRUCT: no 'Verification Commands' section")
    runnable_cmds = [ln for ln in verif.splitlines()
                     if re.search(r"\b(pytest|vitest|npx)\b", ln)]
    if verif and not runnable_cmds:
        findings.append("RUNNABLE: section has no pytest/vitest/npx invocation")

    pytest_files = extract_pytest_files(verif)
    missing_paths = [f for f in pytest_files if not (ROOT / f).exists()]
    if missing_paths:
        findings.append(f"PATH_OK: test files missing on disk: {missing_paths}")

    if m and int(nnn) < 100:
        canon = canonical_test(layer, nnn)
        if not canon.exists():
            findings.append(f"CANON_OK: canonical {canon.relative_to(ROOT)} does not exist")

    mapping = find_section(text, "Test Mapping")
    map_files = extract_mapping_files(mapping)
    verif_files_set = set(pytest_files)
    orphans = [f for f in map_files if f not in verif_files_set]
    if orphans:
        findings.append(f"MAP_OK: in Test Mapping but not verification_commands: {orphans}")

    return {
        "task_id": task_id,
        "card": rel,
        "pytest_files": pytest_files,
        "findings": findings,
        "ok": len(findings) == 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--only", help="filter, e.g. SPEC-D")
    args = ap.parse_args()

    cards = sorted(TASKS.glob("SPEC-*/*.md"))
    if args.only:
        cards = [c for c in cards if args.only in c.as_posix()]

    results = [lint_card(c) for c in cards]

    if args.json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
        return 0 if all(r["ok"] for r in results) else 1

    total = len(results)
    bad = [r for r in results if not r["ok"]]
    by_kind: dict[str, int] = {}
    for r in bad:
        for f in r["findings"]:
            key = f.split(":", 1)[0]
            by_kind[key] = by_kind.get(key, 0) + 1

    print(f"Scanned: {total} cards  |  OK: {total - len(bad)}  |  With findings: {len(bad)}")
    print(f"Finding counts by kind: {by_kind}")
    print("-" * 80)
    for r in bad:
        print(f"\n[{r['task_id']}] {r['card']}")
        for f in r["findings"]:
            print(f"  - {f}")
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
