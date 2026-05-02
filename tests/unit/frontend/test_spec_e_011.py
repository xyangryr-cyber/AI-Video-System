"""Tests for [SPEC-E-011] P4 主播放器 + 下载 + 分段精修面板."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"
PLAYER_TEST = "../../tests/unit/frontend/phase4/MasterAudioPlayer.test.tsx"
PREVIEW_TEST = "../../tests/unit/frontend/phase4/Phase4Preview.test.tsx"
HOOK_TEST = "../../tests/unit/frontend/hooks/useMasterAudioSubscription.test.ts"


def _vitest(file: str, pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1:
    """AC-1: MasterAudioPlayer 渲染 waveform / play/pause / 进度"""

    def test_renders_waveform_play_progress(self):
        r = _vitest(PLAYER_TEST, "AC-1")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2:
    """AC-2: 下载按钮点击触发正确 URL"""

    def test_download_button_calls_correct_url(self):
        r = _vitest(PLAYER_TEST, "AC-2")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3:
    """AC-3: WebSocket master_audio.updated → 重渲"""

    def test_rerenders_on_master_audio_updated(self):
        r1 = _vitest(PLAYER_TEST, "AC-3")
        assert r1.returncode == 0, f"PLAYER stdout={r1.stdout}\nstderr={r1.stderr}"
        r2 = _vitest(HOOK_TEST, "AC-3")
        assert r2.returncode == 0, f"HOOK stdout={r2.stdout}\nstderr={r2.stderr}"


class TestAC4:
    """AC-4: v3.15 分段精修流程不回归"""

    def test_v315_segment_revise_suite(self):
        r = _vitest(PREVIEW_TEST, "AC-4")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5:
    """AC-5: a11y role/aria-label"""

    def test_a11y_role_and_aria_label(self):
        r = _vitest(PLAYER_TEST, "AC-5")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6:
    """AC-6: master_audio 缺失时不报错骨架屏"""

    def test_shows_skeleton_when_master_audio_missing(self):
        r = _vitest(PLAYER_TEST, "AC-6")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
