"""Tests for [SPEC-E-101] PhaseDetailDrawer 7 分块."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"


def _vitest(test_file, pattern):
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, test_file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1:
    """AC-1: 7 分块全部渲染;缺失分块显示空态(不崩)"""

    def test_renders_all_seven_blocks_with_data(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-1 renders all seven blocks with data",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    def test_empty_state_when_phase_data_null(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-1 shows empty state when phaseData is null without crashing",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    def test_empty_state_for_missing_blocks(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-1 shows empty state for missing blocks within phaseData",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2:
    """AC-2: read_only 态所有编辑入口禁用"""

    def test_read_only_indicator_shown(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-2 shows read-only indicator in read_only mode",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    def test_revert_button_only_in_read_only(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-2 revert button is visible only in read_only mode",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    def test_edit_entries_disabled_in_read_only(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-2 hide edit entries in read_only mode via disabled attribute or hidden",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3:
    """AC-3: "从此阶段继续修改" 按钮触发二次确认 + POST /revert"""

    def test_revert_triggers_confirm_then_on_revert(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-3 revert button triggers window.confirm then calls onRevert",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    def test_revert_cancelled_on_confirm_false(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-3 revert button does nothing when confirm is cancelled",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4:
    """AC-4: revert 成功后 current_phase 回退,latest_reached_phase 不变"""

    def test_on_revert_receives_correct_phase(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-4 onRevert receives the correct phase number",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

    def test_drawer_closes_after_successful_revert(self):
        r = _vitest(
            "components/PhaseDetailDrawer.test.tsx",
            "AC-4 drawer closes after successful revert",
        )
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
