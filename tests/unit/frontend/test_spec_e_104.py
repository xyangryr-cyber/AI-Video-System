"""Tests for [SPEC-E-104] ChartConfirmDialog."""

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
    """AC-1: max 2 questions per round; priority time_range/granularity > entity > unit"""

    def test_displays_max_two_questions(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "displays max 2 questions when clarification_questions has 5 items",
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_prioritizes_time_range_granularity_over_entity_unit(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "prioritizes time_range/granularity questions over entity and unit",
        )
        assert r.returncode == 0, r.stdout + r.stderr


class TestAC2:
    """AC-2: unverified source badge red and confirm render button disabled"""

    def test_unverified_badge_red_and_button_disabled(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "shows red badge and disables confirm button when data_source_verified is false",
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_verified_badge_green_and_button_enabled(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "shows green badge and enabled confirm button when data_source_verified is true",
        )
        assert r.returncode == 0, r.stdout + r.stderr


class TestAC3:
    """AC-3: color picker restricted to style_lock.color_palette"""

    def test_color_picker_restricted_to_palette(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "only renders color options from style_lock.color_palette values",
        )
        assert r.returncode == 0, r.stdout + r.stderr


class TestAC4:
    """AC-4: 5 state transitions render correct UI"""

    def test_awaiting_clarification_shows_questions_no_preview(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "awaiting_clarification: shows questions list",
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_awaiting_confirmation_shows_full_editor(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "awaiting_confirmation: shows data preview",
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_rendering_shows_progress_all_disabled(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "rendering: shows progress indicator",
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_done_shows_success_and_close(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "done: shows success message and close button",
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_cancelled_shows_cancel_message_and_close(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "cancelled: shows cancel message and close button",
        )
        assert r.returncode == 0, r.stdout + r.stderr

    def test_confirm_calls_on_confirm_with_overrides(self):
        r = _vitest(
            "components/ChartConfirmDialog.test.tsx",
            "calls onConfirm with overrides when confirm is clicked",
        )
        assert r.returncode == 0, r.stdout + r.stderr
