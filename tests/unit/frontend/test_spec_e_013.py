"""Tests for [SPEC-E-013] P6 全文标注视图 + 编号片段试听 + 最终音频."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"
ANNOTATION_TEST = "../../tests/unit/frontend/phase6/Phase6ScriptAnnotationView.test.tsx"
SEGMENT_TEST = "../../tests/unit/frontend/phase6/Phase6SegmentMixList.test.tsx"
FINAL_TEST = "../../tests/unit/frontend/phase6/Phase6FinalMaster.test.tsx"
PIPELINE_TEST = "../../tests/unit/frontend/phase6/Phase6Pipeline.test.tsx"


def _vitest(file: str, pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1:
    """AC-1: annotation_spans 渲染为带 tooltip 的高亮"""

    def test_renders_highlights_with_tooltip(self):
        r = _vitest(ANNOTATION_TEST, "AC-1")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2:
    """AC-2: 未确认布局 → segment list disabled"""

    def test_disabled_until_confirm_layout(self):
        r = _vitest(SEGMENT_TEST, "AC-2")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3:
    """AC-3: mix_feedback 提交后 segment preview_url 刷新"""

    def test_mix_feedback_refreshes_segment_preview(self):
        r = _vitest(SEGMENT_TEST, "AC-3")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4:
    """AC-4: 最终主播放器仅在 final_audio_master 时出现"""

    def test_only_renders_when_final_kind(self):
        r = _vitest(FINAL_TEST, "AC-4")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5:
    """AC-5: 强制顺序 Step1 → Step2 → Step3"""

    def test_enforces_step1_before_step2(self):
        r = _vitest(PIPELINE_TEST, "AC-5")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6:
    """AC-6: a11y aria-describedby + aria-label"""

    def test_a11y_aria_describedby(self):
        r = _vitest(ANNOTATION_TEST, "AC-6")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
