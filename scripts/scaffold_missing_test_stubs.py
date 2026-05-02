#!/usr/bin/env python3
"""Scaffold canonical test stubs for task cards flagged by lint_task_cards.py.

For each card missing tests/unit/<layer>/test_spec_<x>_<nnn>.py, parse:
  - Title from the H1 line
  - Acceptance Criteria bullets (`- [ ] AC-N: <desc>`)
  - Test Mapping table rows (`| AC-N | <path> | <funcs> |`)

Emit a pytest stub mirroring tests/unit/frontend/test_spec_e_001.py:
  - One `class TestAC<N>:` per AC (docstring carries the AC text)
  - One `def test_<name>(self):` per test function listed in the mapping
  - Body: `pytest.skip("NOT IMPLEMENTED -- waiting for [SPEC-X-NNN]")`

Default mode is --dry-run. Pass --apply to write files.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"

TITLE_RE = re.compile(r"^#\s+\[(SPEC-[A-G]-\d+)\]\s+(.+?)\s*$", re.MULTILINE)
AC_LINE_RE = re.compile(r"^- \[[ xX]\]\s*AC-(\d+)\s*[:：]\s*(.+?)\s*$", re.MULTILINE)
def _section_re(h: str) -> re.Pattern[str]:
    return re.compile(rf"(?ms)^##\s+{re.escape(h)}\s*\n(.*?)(?=\n##\s|\Z)")
MAP_ROW_RE = re.compile(r"^\|\s*AC-(\d+)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$", re.MULTILINE)

FUNC_NAME_RE = re.compile(r"(test_[A-Za-z0-9_]+)")


def get_flagged_cards() -> list[dict[str, Any]]:
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts/lint_task_cards.py"), "--json"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    data = json.loads(proc.stdout)
    return [r for r in data if not r["ok"] and r["pytest_files"]]


def parse_card(card_path: Path) -> dict[str, Any]:
    text = card_path.read_text(encoding="utf-8")
    m = TITLE_RE.search(text)
    task_id = m.group(1) if m else card_path.stem
    title = m.group(2) if m else ""

    ac_section_m = _section_re("Acceptance Criteria").search(text)
    ac_body = ac_section_m.group(1) if ac_section_m else ""
    ac_desc: dict[int, str] = {}
    for m in AC_LINE_RE.finditer(ac_body):
        ac_desc[int(m.group(1))] = m.group(2).strip()

    map_section_m = _section_re("Test Mapping").search(text)
    map_body = map_section_m.group(1) if map_section_m else ""
    ac_funcs: dict[int, list[str]] = OrderedDict()
    for m in MAP_ROW_RE.finditer(map_body):
        n = int(m.group(1))
        funcs_cell = m.group(3)
        names = FUNC_NAME_RE.findall(funcs_cell)
        bucket = ac_funcs.setdefault(n, [])
        for name in names:
            if name not in bucket:
                bucket.append(name)

    return {
        "task_id": task_id,
        "title": title,
        "ac_desc": ac_desc,
        "ac_funcs": ac_funcs,
    }


def render_stub(card: dict[str, Any]) -> str:
    task_id = card["task_id"]
    title = card["title"]
    ac_desc = card["ac_desc"]
    ac_funcs = card["ac_funcs"]

    all_acs = sorted(set(ac_desc) | set(ac_funcs))

    lines: list[str] = []
    header = f'"""Tests for [{task_id}] {title}."""' if title else f'"""Tests for [{task_id}]."""'
    lines.append(header)
    lines.append("import pytest")
    lines.append("")

    if not all_acs:
        lines.append("")
        lines.append("class TestPlaceholder:")
        lines.append('    """Stub: task card has no ACs; regenerate after updating card."""')
        lines.append("")
        lines.append("    def test_placeholder(self):")
        lines.append(f'        pytest.skip("NOT IMPLEMENTED -- waiting for [{task_id}]")')
        return "\n".join(lines) + "\n"

    for n in all_acs:
        desc = ac_desc.get(n, "(no description in Acceptance Criteria)")
        funcs = ac_funcs.get(n, [f"test_ac_{n}"])
        safe_desc = desc.replace('"""', '\\"\\"\\"')
        if safe_desc.endswith('"'):
            safe_desc = safe_desc + " "
        lines.append("")
        lines.append("")
        lines.append(f"class TestAC{n}:")
        lines.append(f'    """AC-{n}: {safe_desc}"""')
        for fn in funcs:
            lines.append("")
            lines.append(f"    def {fn}(self):")
            lines.append(f'        pytest.skip("NOT IMPLEMENTED -- waiting for [{task_id}]")')

    return "\n".join(lines) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="filter, e.g. SPEC-D")
    ap.add_argument("--show", type=int, default=1, help="print generated content for first N stubs")
    args = ap.parse_args()

    flagged = get_flagged_cards()
    if args.only:
        flagged = [r for r in flagged if args.only in r["card"]]

    shown = 0
    created = 0
    skipped = 0
    for row in flagged:
        card_path = ROOT / row["card"]
        canonical_rel = row["pytest_files"][0]
        canonical_path = ROOT / canonical_rel

        if canonical_path.exists():
            skipped += 1
            continue

        card = parse_card(card_path)
        content = render_stub(card)

        if shown < args.show:
            bar = "=" * 80
            print(bar)
            print(f"{canonical_rel}   <-   {row['card']}")
            print(bar)
            print(content)
            shown += 1

        if args.apply:
            canonical_path.parent.mkdir(parents=True, exist_ok=True)
            canonical_path.write_text(content, encoding="utf-8")
            print(f"created: {canonical_rel}")
            created += 1
        else:
            print(f"would create: {canonical_rel}")
            created += 1

    print("-" * 80)
    mode = "applied" if args.apply else "dry-run"
    print(f"[{mode}] {created} stubs generated, {skipped} already existed, {len(flagged)} flagged.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
