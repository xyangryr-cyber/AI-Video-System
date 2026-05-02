"""Tests for [SPEC-F-004] EChartsFrameController (Remotion Context)."""

from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
FRONTEND = REPO / "src" / "frontend"
ECHARTS_DIR = FRONTEND / "components" / "templates" / "echarts"
FRAME_CONTROLLER = ECHARTS_DIR / "EChartsFrameController.tsx"
USE_FRAME_HOOK = ECHARTS_DIR / "useEChartsFrame.ts"


def _read_src(filepath: Path) -> str:
    """Read a TS/TSX source file if it exists."""
    if not filepath.exists():
        return ""
    return filepath.read_text()


def _read_controller() -> str:
    return _read_src(FRAME_CONTROLLER)


def _read_hook() -> str:
    return _read_src(USE_FRAME_HOOK)


# ---------------------------------------------------------------------------
# AC-1: EChartsFrameController initializes with animation: false
# ---------------------------------------------------------------------------
class TestAC1AnimationDisabledOnInit:
    """AC-1: EChartsFrameController initializes with `animation: false`"""

    def test_animation_disabled_on_init(self):
        src = _read_controller()
        assert src, "EChartsFrameController.tsx does not exist or is empty"
        # Must set animation: false (not animation: true) in the option
        assert "animation: false" in src, (
            "EChartsFrameController must set 'animation: false' in ECharts option"
        )

    def test_no_animation_true_in_option(self):
        src = _read_controller()
        assert src, "EChartsFrameController.tsx does not exist or is empty"
        # The option object built for setOption must not contain animation: true
        # (allow "animation: true" only in comments)
        lines = [
            l
            for l in src.split("\n")
            if "animation: true" in l and not l.strip().startswith("//")
        ]
        assert len(lines) == 0, (
            "EChartsFrameController must not use 'animation: true' in option"
        )


# ---------------------------------------------------------------------------
# AC-2: Same-frame double render produces identical PNG SHA256
# ---------------------------------------------------------------------------
class TestAC2DeterministicRenderSha256:
    """AC-2: Same-frame double render produces identical PNG SHA256"""

    def test_pure_computation_no_random(self):
        """Frame state computation must be deterministic — no Math.random()."""
        src = _read_hook()
        assert src, "useEChartsFrame.ts does not exist or is empty"
        assert "Math.random" not in src, (
            "useEChartsFrame must not use Math.random() — computation must be deterministic"
        )

    def test_pure_computation_no_date(self):
        """Frame state computation must be deterministic — no Date.now()."""
        src = _read_hook()
        assert src, "useEChartsFrame.ts does not exist or is empty"
        assert "Date.now" not in src, (
            "useEChartsFrame must not use Date.now() — computation must be deterministic"
        )

    def test_compute_frame_state_exported(self):
        """A pure computeFrameState function must be exported for testability."""
        src = _read_hook()
        assert src, "useEChartsFrame.ts does not exist or is empty"
        assert "export" in src and "computeFrameState" in src, (
            "useEChartsFrame must export a pure 'computeFrameState' function"
        )


# ---------------------------------------------------------------------------
# AC-3: pause_trigger activates when Math.abs(easedProgress - trigger.at_progress) < 0.01
# ---------------------------------------------------------------------------
class TestAC3PauseTriggerThreshold:
    """AC-3: Pause trigger activates at threshold 0.01"""

    def test_pause_trigger_threshold_math_abs(self):
        src = _read_hook()
        assert src, "useEChartsFrame.ts does not exist or is empty"
        assert "Math.abs" in src, (
            "Pause trigger detection must use Math.abs for threshold comparison"
        )

    def test_pause_trigger_threshold_value(self):
        src = _read_hook()
        assert src, "useEChartsFrame.ts does not exist or is empty"
        # The threshold must be 0.01 as specified in the task card
        assert "0.01" in src, "Pause trigger threshold must be 0.01"

    def test_pause_trigger_references_at_progress(self):
        src = _read_hook()
        assert src, "useEChartsFrame.ts does not exist or is empty"
        assert "at_progress" in src, (
            "Pause trigger detection must reference 'at_progress' field"
        )


# ---------------------------------------------------------------------------
# AC-4: During pause, onFrame stops calling setOption; ECharts holds state
# ---------------------------------------------------------------------------
class TestAC4PauseFreezesSetoption:
    """AC-4: During pause, `onFrame` stops calling `setOption`"""

    def test_pause_skips_setoption(self):
        src = _read_controller()
        assert src, "EChartsFrameController.tsx does not exist or is empty"
        # Controller must have conditional logic that skips setOption during pause
        assert "isPaused" in src, "EChartsFrameController must check 'isPaused' state"
        assert "setOption" in src, (
            "EChartsFrameController must call setOption (conditional on pause state)"
        )

    def test_pause_guard_before_setoption(self):
        """Controller must guard setOption with isPaused check — either
        early-return or conditional block."""
        src = _read_controller()
        assert src, "EChartsFrameController.tsx does not exist or is empty"
        # The implementation must check isPaused before calling setOption.
        # Accept both patterns: early-return `if (isPaused) return` or
        # conditional `if (!isPaused) { ... setOption }`.
        has_guard = (
            "if (isPaused)" in src
            or "if (!isPaused)" in src
            or "if (frameState.isPaused)" in src
            or "if (!frameState.isPaused)" in src
        )
        assert has_guard, (
            "EChartsFrameController must guard setOption with an isPaused check"
        )


# ---------------------------------------------------------------------------
# AC-5: After pause resume, rendering continues from correct position
# ---------------------------------------------------------------------------
class TestAC5ResumeFromCorrectPosition:
    """AC-5: After pause resume, rendering continues from correct position"""

    def test_pause_frame_accumulation(self):
        """Frame computation must track total pause frames to offset progress."""
        src = _read_hook()
        assert src, "useEChartsFrame.ts does not exist or is empty"
        # Must accumulate pause frames so progress resumes from correct position
        assert "duration_sec" in src, (
            "useEChartsFrame must reference 'duration_sec' for pause duration calculation"
        )

    def test_data_index_calculation(self):
        """Must calculate data index from eased progress."""
        src = _read_hook()
        assert src, "useEChartsFrame.ts does not exist or is empty"
        assert "dataIndex" in src or "data_index" in src, (
            "useEChartsFrame must compute data index from eased progress"
        )


# ---------------------------------------------------------------------------
# AC-6: Frame formula `frame = timeSec * fps` produces integer frames
# ---------------------------------------------------------------------------
class TestAC6FrameFormulaInteger:
    """AC-6: Frame formula `frame = timeSec * fps` produces integer frames"""

    def test_frame_formula_integer_floor(self):
        """Frame must be converted to integer via Math.floor or Math.round."""
        src = _read_hook()
        assert src, "useEChartsFrame.ts does not exist or is empty"
        has_floor = "Math.floor" in src or "Math.round" in src or "Math.trunc" in src
        assert has_floor, (
            "useEChartsFrame must use Math.floor/round/trunc to produce integer frames"
        )
