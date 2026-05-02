"""Tests for [SPEC-E-103] StoryboardEditor anchor + shot split UI."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"


def _vitest(test_file: str, pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, test_file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1:
    """AC-1: Selecting a shot auto-highlights anchor_text interval in left panel."""

    def test_selecting_shot_highlights_anchor_text_range(self):
        r = _vitest("components/StoryboardEditor.test.tsx", "AC-1")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2:
    """AC-2: Drag-split produces callback; parent shot retained as split_from_shot_id."""

    def test_drag_split_creates_two_shots_with_parent_lineage(self):
        r = _vitest("components/StoryboardEditor.test.tsx", "AC-2")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3:
    """AC-3: After split, child shot durations sum = parent within 100ms."""

    def test_child_shot_durations_sum_equals_parent_within_100ms(self):
        r = _vitest("components/StoryboardEditor.test.tsx", "AC-3")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4:
    """AC-4: Shot card renders scene_type/duration/claim count/placeholder preview/mode chip."""

    def test_shot_card_renders_scene_type_duration_claim_preview_mode(self):
        r = _vitest("components/StoryboardEditor.test.tsx", "AC-4")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
