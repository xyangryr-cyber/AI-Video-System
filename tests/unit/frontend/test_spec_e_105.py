"""Tests for [SPEC-E-105] PreferenceWritebackCard + SafetyResponseCard."""

import subprocess
from pathlib import Path


FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"
TEST_FILE = "components/PreferenceSafetyCards.test.tsx"


def _vitest(test_file: str, pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, test_file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1:
    """AC-1: 三栏对比 `当前 vs 历史 vs 推荐`;批量勾选 + 一键保存"""

    def test_three_column_compare_and_batch_save(self):
        r = _vitest(TEST_FILE, "AC-1 PreferenceWritebackCard 3-column comparison")
        assert r.returncode == 0, r.stdout + r.stderr


class TestAC2:
    """AC-2: SafetyResponseCard 显示分类标签 + 模板话术,不显示原始 user input"""

    def test_safety_card_shows_template_not_raw_input(self):
        r = _vitest(TEST_FILE, "AC-2 SafetyResponseCard shows template not raw input")
        assert r.returncode == 0, r.stdout + r.stderr


class TestAC3:
    """AC-3: "为什么这个回复"折叠区展示 policy 决策依据(template_id)"""

    def test_why_this_reply_collapsible_shows_template_id(self):
        r = _vitest(TEST_FILE, "AC-3 Why this reply collapsible")
        assert r.returncode == 0, r.stdout + r.stderr


class TestAC4:
    """AC-4: a11y:aria-label / 键盘导航可用"""

    def test_a11y_aria_label_and_keyboard_navigation(self):
        r = _vitest(TEST_FILE, "AC-4 a11y aria-label and keyboard navigation")
        assert r.returncode == 0, r.stdout + r.stderr
