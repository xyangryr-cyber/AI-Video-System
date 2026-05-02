"""[SPEC-C-008] IntentRouter Accuracy Eval Test Set."""

import json
import os
import subprocess
import sys
from pathlib import Path


EVAL_DIR = Path("tests/eval")
JSONL_PATH = EVAL_DIR / "router.jsonl"
EVAL_SCRIPT = EVAL_DIR / "eval_router.py"

ACTION_TYPES = (
    "revise",
    "regenerate_section",
    "regenerate_shot",
    "challenge_claim",
    "supplement_claim",
    "request_chart",
    "view_phase_detail",
    "save_stage_preference",
    "insert_section",
    "clarify",
)


class TestAC1JsonlHas100Entries:
    def test_jsonl_has_100_entries(self):
        assert JSONL_PATH.exists(), f"{JSONL_PATH} not found"
        entries = [json.loads(line) for line in open(JSONL_PATH) if line.strip()]
        assert len(entries) == 100, f"Expected 100 entries, got {len(entries)}"


class TestAC2EachActionTypeMin10:
    def test_each_action_type_min_10(self):
        entries = [json.loads(line) for line in open(JSONL_PATH) if line.strip()]
        counts = {}
        for e in entries:
            action = e.get("expected_action", "")
            counts[action] = counts.get(action, 0) + 1
        for action in ACTION_TYPES:
            assert counts.get(action, 0) >= 10, (
                f"Action '{action}' has {counts.get(action, 0)} entries, need >=10"
            )


class TestAC3EvalProducesAccuracy:
    def test_eval_produces_accuracy(self):
        result = subprocess.run(
            [sys.executable, str(EVAL_SCRIPT), "--report"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        assert result.returncode == 0, f"Eval script failed: {result.stderr}"
        assert (
            "overall_accuracy" in result.stdout.lower()
            or "accuracy" in result.stdout.lower()
        ), f"Output missing accuracy: {result.stdout}"


class TestAC4OverallAccuracyGe85:
    def test_overall_accuracy_ge_85(self):
        result = subprocess.run(
            [sys.executable, str(EVAL_SCRIPT), "--report"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        output = result.stdout + result.stderr
        # Parse accuracy from output like "Overall accuracy: 95.00%"
        import re

        m = re.search(
            r"(?:overall|total).*?accuracy.*?(\d+\.?\d*)\s*%", output, re.IGNORECASE
        )
        assert m is not None, f"Cannot parse accuracy from: {output}"
        acc = float(m.group(1))
        assert acc >= 85.0, f"Overall accuracy {acc}% < 85%"


class TestAC5PerActionAccuracyGe70:
    def test_per_action_accuracy_ge_70(self):
        result = subprocess.run(
            [sys.executable, str(EVAL_SCRIPT), "--report"],
            capture_output=True,
            text=True,
            cwd=os.getcwd(),
        )
        output = result.stdout + result.stderr
        import re

        # Parse per-action accuracies like "revise: 90.00%"
        per_action = {}
        for line in output.splitlines():
            m = re.match(r"\s*(\w+):\s*(\d+\.?\d*)\s*%", line)
            if m:
                per_action[m.group(1)] = float(m.group(2))
        for action in ACTION_TYPES:
            acc = per_action.get(action)
            assert acc is not None, f"No accuracy reported for action '{action}'"
            assert acc >= 70.0, f"Action '{action}' accuracy {acc}% < 70%"
