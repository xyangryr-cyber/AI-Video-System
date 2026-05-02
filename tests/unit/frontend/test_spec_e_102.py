"""Tests for [SPEC-E-102] Claim Workbench (supersedes SPEC-2.7 DataVerificationPanel)."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"


def _vitest(test_file: str, pattern: str):
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, test_file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1:
    """AC-1: 4 filter dimensions return correct subset."""

    def test_filter_bar_four_dimensions_returns_correct_subset(self):
        r = _vitest("components/ClaimWorkbench.test.tsx", "AC-1:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2:
    """AC-2: 4 row-level operations trigger correct actions."""

    def test_row_actions_trigger_corresponding_actions(self):
        r = _vitest("components/ClaimWorkbench.test.tsx", "AC-2:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3:
    """AC-3: hard blocking badge turns red when unverified > 0."""

    def test_blocking_badge_turns_red_when_hard_unverified_gt_zero(self):
        r = _vitest("components/ClaimWorkbench.test.tsx", "AC-3:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4:
    """AC-4: view toggle preserves filter state."""

    def test_view_toggle_preserves_filter_state(self):
        r = _vitest("components/ClaimWorkbench.test.tsx", "AC-4:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
