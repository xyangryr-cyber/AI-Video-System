#!/usr/bin/env python3
"""Rewrite task card test-file paths to canonical tests/unit/<layer>/test_spec_<x>_<nnn>.py.

For each card:
  - Verification Commands: collapse all pytest/vitest lines into ONE canonical
    `pytest <canonical> -v` line; keep non-test commands (docker/curl/mypy/tsc) intact.
  - Test Mapping table: rewrite every Test File cell to the canonical path.

Default mode is --dry-run. Pass --apply to write changes.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS = ROOT / "tasks"

LAYER_DIR = {
    "A": "contracts",
    "B": "infra",
    "C": "backend-core",
    "D": "pipeline",
    "E": "frontend",
    "F": "media-render",
    "G": "workers",
}

TASK_ID_RE = re.compile(r"SPEC-([A-G])-(\d+)")
PYTEST_LINE_RE = re.compile(
    r"^\s*(?:pytest|vitest(?:\s+run)?|npx\s+vitest(?:\s+run)?)\s+\S+.*$",
    re.MULTILINE,
)
TEST_PATH_CELL_RE = re.compile(r"(tests/[\w/.\-]+\.(?:py|tsx?|ts))")


def canonical_path(layer: str, nnn: str) -> str:
    sub = LAYER_DIR[layer.upper()]
    return f"tests/unit/{sub}/test_spec_{layer.lower()}_{int(nnn):03d}.py"


def rewrite_verification(section_body: str, canonical: str) -> str:
    lines = section_body.splitlines()
    new: list[str] = []
    pytest_emitted = False
    for ln in lines:
        if PYTEST_LINE_RE.match(ln):
            if not pytest_emitted:
                m = re.match(r"^(\s*)", ln)
                indent = m.group(1) if m else ""
                new.append(f"{indent}pytest {canonical} -v")
                pytest_emitted = True
            continue
        new.append(ln)
    if not pytest_emitted:
        insert_at = 0
        for i, ln in enumerate(new):
            if ln.strip().startswith("```bash"):
                insert_at = i + 1
                break
        new.insert(insert_at, f"pytest {canonical} -v")
    return "\n".join(new)


def rewrite_mapping(section_body: str, canonical: str) -> str:
    return TEST_PATH_CELL_RE.sub(canonical, section_body)


def replace_section(text: str, header: str, new_body: str) -> str:
    pattern = rf"(?ms)^(##\s+{re.escape(header)}\s*\n)(.*?)(?=\n##\s|\Z)"
    m = re.search(pattern, text)
    if not m:
        return text
    return text[:m.start(2)] + new_body + text[m.end(2):]


def compute_new_text(text: str) -> tuple[str, str | None]:
    """Return (new_text, canonical_path or None if no task id)."""
    m = TASK_ID_RE.search(text)
    if not m:
        return text, None
    layer, nnn = m.group(1), m.group(2)
    canonical = canonical_path(layer, nnn)

    verif_re = re.compile(r"(?ms)^##\s+Verification Commands\s*\n(.*?)(?=\n##\s|\Z)")
    map_re = re.compile(r"(?ms)^##\s+Test Mapping\s*\n(.*?)(?=\n##\s|\Z)")

    def keep_trailing(original_body: str, rewritten_body: str) -> str:
        if original_body.endswith("\n") and not rewritten_body.endswith("\n"):
            return rewritten_body + "\n"
        return rewritten_body

    new_text = text
    vm = verif_re.search(new_text)
    if vm:
        new_verif = keep_trailing(vm.group(1), rewrite_verification(vm.group(1), canonical))
        new_text = replace_section(new_text, "Verification Commands", new_verif)
    mm = map_re.search(new_text)
    if mm:
        new_map = keep_trailing(mm.group(1), rewrite_mapping(mm.group(1), canonical))
        new_text = replace_section(new_text, "Test Mapping", new_map)
    return new_text, canonical


def main() -> int:
    import difflib
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--only", help="filter, e.g. SPEC-D")
    ap.add_argument("--show", type=int, default=0, help="print diff for first N changed cards")
    args = ap.parse_args()

    cards = sorted(TASKS.glob("SPEC-*/*.md"))
    if args.only:
        cards = [c for c in cards if args.only in c.as_posix()]

    changed = 0
    shown = 0
    for c in cards:
        original = c.read_text(encoding="utf-8")
        new_text, canonical = compute_new_text(original)
        if canonical is None:
            print(f"SKIP (no task id): {c.name}")
            continue
        if new_text == original:
            print(f"unchanged: {c.relative_to(ROOT)}")
            continue

        changed += 1
        if args.apply:
            c.write_text(new_text, encoding="utf-8")
            print(f"rewrote:   {c.relative_to(ROOT)}  -> {canonical}")
        else:
            print(f"would rewrite: {c.relative_to(ROOT)}  -> {canonical}")
            if shown < args.show:
                diff = difflib.unified_diff(
                    original.splitlines(keepends=True),
                    new_text.splitlines(keepends=True),
                    fromfile=str(c.relative_to(ROOT)) + " (before)",
                    tofile=str(c.relative_to(ROOT)) + " (after)",
                )
                sys.stdout.writelines(diff)
                shown += 1
    print("-" * 80)
    mode = "applied" if args.apply else "dry-run"
    print(f"[{mode}] {changed}/{len(cards)} cards changed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
