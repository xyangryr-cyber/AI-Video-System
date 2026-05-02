#!/usr/bin/env python3
"""Pick the next executable task from tasks/ + PROGRESS.md.

Returns the lowest-id P0 task whose status is not DONE/IN_PROGRESS/SKIPPED
and whose declared depends_on tasks are all DONE. Exits 1 and prints nothing
if no task is currently ready.

Used by the outer driver loop (mode B): each iteration starts a fresh
`claude -p` with the picked task id, so context never grows across tasks.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

TASK_ID_RE = re.compile(r"SPEC-[A-G]-\d{3}(?:-?[a-z]+)?")
PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}


@dataclass
class TaskCard:
    task_id: str
    depends_on: list[str]
    priority: str
    allowed_files: list[str]
    bdd_tags: list[str]


def _metadata_value(body: str, key: str) -> str | None:
    m = re.search(
        rf"^\s*-\s+\*\*{re.escape(key)}\*\*:\s*(.+?)\s*$",
        body,
        re.MULTILINE,
    )
    return m.group(1).strip() if m else None


def _parse_depends_on(raw: str | None) -> list[str]:
    if not raw:
        return []
    return TASK_ID_RE.findall(raw)


def _parse_bdd_tags(raw: str | None) -> list[str]:
    """Parse `- **bdd_tags**: [@router, @phase0]` into a list.

    Tags must start with '@'. Returns [] if key absent or malformed.
    """
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        parts = [p.strip().strip("'\"") for p in inner.split(",")]
    else:
        parts = [p.strip() for p in raw.split(",")]
    return [p for p in parts if p.startswith("@")]


def _parse_allowed_files(raw: str | None) -> list[str]:
    """Parse `- **allowed_files**: [a.py, b.py]` or YAML list form."""
    if not raw:
        return []
    raw = raw.strip()
    if raw.startswith("[") and raw.endswith("]"):
        inner = raw[1:-1].strip()
        if not inner:
            return []
        return [p.strip().strip("'\"") for p in inner.split(",") if p.strip()]
    return [p.strip() for p in raw.split(",") if p.strip()]


def load_task_cards(root: Path) -> dict[str, TaskCard]:
    cards: dict[str, TaskCard] = {}
    for spec_dir in sorted((root / "tasks").glob("SPEC-*")):
        if not spec_dir.is_dir():
            continue
        for card_path in sorted(spec_dir.glob("*.md")):
            body = card_path.read_text(encoding="utf-8")
            task_id = _metadata_value(body, "task_id")
            if not task_id or not TASK_ID_RE.fullmatch(task_id):
                continue
            depends_on = _parse_depends_on(
                _metadata_value(body, "depends_on")
            )
            raw_priority = (_metadata_value(body, "priority") or "P2").strip()
            priority_match = re.match(r"(P[0-3])", raw_priority)
            priority = priority_match.group(1) if priority_match else "P2"
            allowed = _parse_allowed_files(
                _metadata_value(body, "allowed_files")
            )
            bdd_tags = _parse_bdd_tags(
                _metadata_value(body, "bdd_tags")
            )
            cards[task_id] = TaskCard(
                task_id=task_id,
                depends_on=depends_on,
                priority=priority,
                allowed_files=allowed,
                bdd_tags=bdd_tags,
            )
    return cards


_TABLE_ROW_RE = re.compile(r"^\|.*$", re.MULTILINE)
_TABLE_TASK_ID_RE = re.compile(r"(SPEC-([A-G])-(\d{3})(?:-?[a-z]+)?)((?:/\d{3})*)")
_SNAPSHOT_ROW_RE = re.compile(
    r"^\|\s*([A-G])\s+--\s+[^|]*\|([^|]*)\|", re.MULTILINE
)
_SNAPSHOT_RANGE_RE = re.compile(r"(\d{3})\s*\.\.\s*(?:[A-Z]-)?(\d{3})")


def _parse_done_from_tables(text: str) -> set[str]:
    """DONE task ids from PROGRESS.md v1.1.0 markdown tables.

    Two table shapes are recognized:
    - Recent commits rows: any `SPEC-X-NNN` in a `|`-row counts as DONE.
      Shorthand `SPEC-X-NNN/MMM/...` expands — each trailing `/NNN` inherits
      the X prefix (so `SPEC-A-001/002/004` -> {A-001, A-002, A-004}).
    - Status snapshot rows shaped `| X -- Label | A-001, A-002, ... | ... |`
      where X is one of A..F: every short-form `NNN` in column 2 expands to
      `SPEC-{X}-{NNN}`. Range form `NNN..MMM` (or `NNN..X-MMM`) expands to the
      inclusive integer range — without this, `A-001..A-018` would only
      register A-001 and A-018 as DONE and silently drop A-002..A-017.

    Bullet lines in "Open follow-ups" are ignored (they don't start with `|`).
    """
    done: set[str] = set()
    for row in _TABLE_ROW_RE.findall(text):
        for m in _TABLE_TASK_ID_RE.finditer(row):
            full_id, letter, _base, extras = m.group(1), m.group(2), m.group(3), m.group(4)
            done.add(full_id)
            for num in re.findall(r"\d{3}", extras):
                done.add(f"SPEC-{letter}-{num}")
    for m in _SNAPSHOT_ROW_RE.finditer(text):
        letter, col2 = m.group(1), m.group(2)
        for r in _SNAPSHOT_RANGE_RE.finditer(col2):
            start, end = int(r.group(1)), int(r.group(2))
            if start <= end:
                for n in range(start, end + 1):
                    done.add(f"SPEC-{letter}-{n:03d}")
        for num in re.findall(r"\b(\d{3})\b", col2):
            done.add(f"SPEC-{letter}-{num}")
    return done


def load_statuses(root: Path) -> dict[str, str]:
    """Latest status per task_id from PROGRESS.md.

    Two formats supported:
    1. Legacy (pre-2026-04-20 archives + unit-test fixtures):
       `## [SPEC-X-NNN] ...` section with `**Status**: DONE|IN_PROGRESS|SKIPPED`.
       Later entries override earlier ones.
    2. v1.1.0 index (HARNESS §9.2): markdown tables ("Recent commits",
       "Status snapshot"). Any SPEC-X-NNN in a table row = DONE.

    Explicit legacy status wins over table-inferred DONE (so a task the old
    format marks IN_PROGRESS/SKIPPED stays that way even if it also shows up
    in a commit row).
    """
    progress = root / "PROGRESS.md"
    if not progress.exists():
        return {}
    text = progress.read_text(encoding="utf-8")
    entry_re = re.compile(
        r"^##\s+\[(SPEC-[A-G]-\d{3})\][^\n]*\n(.*?)(?=^##\s|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    statuses: dict[str, str] = {}
    for m in entry_re.finditer(text):
        task_id = m.group(1)
        status_m = re.search(r"\*\*Status\*\*:\s*([A-Z_]+)", m.group(2))
        if status_m:
            statuses[task_id] = status_m.group(1).strip()
    for tid in _parse_done_from_tables(text):
        statuses.setdefault(tid, "DONE")
    return statuses


def _ready_cards_sorted(root: Path) -> list[TaskCard]:
    cards = load_task_cards(root)
    statuses = load_statuses(root)
    done = {tid for tid, s in statuses.items() if s == "DONE"}
    unpickable = {
        tid
        for tid, s in statuses.items()
        if s in {"DONE", "IN_PROGRESS", "SKIPPED"}
    }
    ready: list[TaskCard] = []
    for card in cards.values():
        if card.task_id in unpickable:
            continue
        if not all(dep in done for dep in card.depends_on):
            continue
        ready.append(card)
    ready.sort(
        key=lambda c: (
            PRIORITY_ORDER.get(c.priority, 99),
            c.task_id,
        )
    )
    return ready


def pick_next(root: Path) -> str | None:
    ready = _ready_cards_sorted(root)
    if not ready:
        return None
    return ready[0].task_id


def pick_next_batch(root: Path, limit: int) -> list[str]:
    """Return up to `limit` ready task ids with pairwise-disjoint allowed_files.

    Greedy: walk priority-sorted ready list, accept a card if its allowed_files
    do not intersect any already-accepted card. Cards with empty allowed_files
    are treated as "touches everything" and thus only the first such card is
    accepted — safer default than assuming empty = touches nothing.
    """
    if limit <= 0:
        return []
    ready = _ready_cards_sorted(root)
    accepted: list[TaskCard] = []
    claimed: set[str] = set()
    has_unbounded_accepted = False
    for card in ready:
        if len(accepted) >= limit:
            break
        files = set(card.allowed_files)
        if not files:
            if has_unbounded_accepted or accepted:
                continue
            has_unbounded_accepted = True
            accepted.append(card)
            continue
        if files & claimed:
            continue
        if has_unbounded_accepted:
            continue
        accepted.append(card)
        claimed |= files
    return [c.task_id for c in accepted]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Print the next executable SPEC task id."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parent.parent,
        help="Project root (defaults to script parent directory).",
    )
    parser.add_argument(
        "--task-id",
        default=None,
        help=(
            "Override dependency/status ordering: print this id if the card "
            "exists, else exit 1. Driver uses this to target a specific task."
        ),
    )
    args = parser.parse_args(argv)
    if args.task_id is not None:
        cards = load_task_cards(args.root)
        if args.task_id not in cards:
            return 1
        print(args.task_id)
        return 0
    task_id = pick_next(args.root)
    if task_id is None:
        return 1
    print(task_id)
    return 0


if __name__ == "__main__":
    sys.exit(main())
