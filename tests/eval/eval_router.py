"""[SPEC-C-008] Router eval script.

Usage: python tests/eval/eval_router.py --report
"""

from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

# Ensure the project root is on sys.path for imports.
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from src.backend.agents.intent_router import IntentRouter


JSONL_PATH = Path(__file__).resolve().parent / "router.jsonl"


def load_entries(path: Path | None = None) -> list[dict]:
    path = path or JSONL_PATH
    entries = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                entries.append(json.loads(line))
    return entries


def run_eval(entries: list[dict]) -> dict:
    router = IntentRouter()
    correct = 0
    total = len(entries)
    per_action = defaultdict(lambda: {"correct": 0, "total": 0})

    for entry in entries:
        expected = entry["expected_action"]
        raw = entry.get("raw_output")
        result = router.parse_or_fallback(raw)
        predicted = result["action"]
        per_action[expected]["total"] += 1
        if predicted == expected:
            correct += 1
            per_action[expected]["correct"] += 1

    overall = (correct / total * 100) if total > 0 else 0.0
    per_action_acc = {
        action: (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0.0
        for action, stats in per_action.items()
    }
    return {
        "overall_accuracy": overall,
        "per_action": per_action_acc,
        "total": total,
        "correct": correct,
    }


def report(entries: list[dict] | None = None) -> str:
    if entries is None:
        entries = load_entries()
    results = run_eval(entries)
    lines = [
        f"Total entries: {results['total']}",
        f"Correct: {results['correct']}",
        f"Overall accuracy: {results['overall_accuracy']:.2f}%",
        "",
    ]
    for action, acc in sorted(results["per_action"].items()):
        lines.append(f"{action}: {acc:.2f}%")
    return "\n".join(lines)


if __name__ == "__main__":
    entries = load_entries()
    if "--report" in sys.argv or len(sys.argv) == 1:
        print(report(entries))
