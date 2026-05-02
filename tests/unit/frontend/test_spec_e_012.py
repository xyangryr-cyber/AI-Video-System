"""Tests for [SPEC-E-012] P5 混音预览 + 候选比较 + 主播放器."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"
CARD_TEST = "../../tests/unit/frontend/phase5/Phase5CandidateCard.test.tsx"
MASTER_TEST = "../../tests/unit/frontend/phase5/Phase5MasterPlayer.test.tsx"


def _vitest(file: str, pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1:
    """AC-1: 候选卡片同时渲染 preview / raw 两个播放器入口"""

    def test_renders_preview_and_raw_buttons(self):
        r = _vitest(CARD_TEST, "AC-1")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2:
    """AC-2: 选定候选 → store master_audio 切换；MasterPlayer 出现 + 下载"""

    def test_select_candidate_shows_master_and_download(self):
        r1 = _vitest(CARD_TEST, "AC-2")
        r2 = _vitest(MASTER_TEST, "AC-2")
        assert r1.returncode == 0, f"CARD stdout={r1.stdout}\nstderr={r1.stderr}"
        assert r2.returncode == 0, f"MASTER stdout={r2.stdout}\nstderr={r2.stderr}"


class TestAC3:
    """AC-3: 选 "无 BGM" → store master_audio.kind=narration_master"""

    def test_no_bgm_falls_back_to_narration(self):
        r = _vitest(MASTER_TEST, "AC-3")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4:
    """AC-4: A/B 切换不打断当前播放"""

    def test_ab_switch_does_not_break_play(self):
        r = _vitest(CARD_TEST, "AC-4")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5:
    """AC-5: fit_review 聚合 PASS/FAIL 徽章"""

    def test_renders_fit_review_aggregate_badge(self):
        r = _vitest(CARD_TEST, "AC-5")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6:
    """AC-6: a11y role="article" + aria-pressed"""

    def test_a11y_role_and_aria_pressed(self):
        r1 = _vitest(CARD_TEST, "AC-6")
        r2 = _vitest(MASTER_TEST, "AC-6")
        assert r1.returncode == 0, f"CARD stdout={r1.stdout}\nstderr={r1.stderr}"
        assert r2.returncode == 0, f"MASTER stdout={r2.stdout}\nstderr={r2.stderr}"
