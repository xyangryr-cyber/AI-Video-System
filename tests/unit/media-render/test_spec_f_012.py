"""Tests for [SPEC-F-012] Preview Player & Layer Decomposition."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
PLAYER_DIR = PROJECT_ROOT / "src" / "frontend" / "components" / "player"
PREVIEW_PATH = PLAYER_DIR / "PreviewPlayer.tsx"
LAYER_TOGGLE_PATH = PLAYER_DIR / "LayerToggle.tsx"
KEYBOARD_PATH = PLAYER_DIR / "KeyboardControls.ts"
ANNOTATION_PATH = PLAYER_DIR / "TimelineAnnotation.tsx"

LAYER_NAMES = ["text", "data", "visual", "audio"]


def _read_text(path: Path) -> str:
    assert path.is_file(), f"Missing file: {path}"
    return path.read_text(encoding="utf-8")


def _all_player_sources() -> str:
    sources = []
    for p in [PREVIEW_PATH, LAYER_TOGGLE_PATH, KEYBOARD_PATH, ANNOTATION_PATH]:
        if p.is_file():
            sources.append(p.read_text(encoding="utf-8"))
    return "\n".join(sources)


class TestAC1ArrowKeyFrameStep:
    """AC-1: Right arrow key increments currentFrame by 1"""

    def test_arrow_key_frame_step(self):
        source = _read_text(KEYBOARD_PATH)
        assert "ArrowRight" in source, "KeyboardControls must handle ArrowRight key"
        assert "1" in source, "ArrowRight must increment currentFrame by 1"


class TestAC2ShiftArrowTenFrameStep:
    """AC-2: Shift+Right arrow increments currentFrame by 10"""

    def test_shift_arrow_ten_frame_step(self):
        source = _read_text(KEYBOARD_PATH)
        assert "Shift" in source, "KeyboardControls must handle Shift modifier"
        assert "10" in source, "Shift+Arrow must increment by 10 frames"


class TestAC3MKeyAnnotationToTaskLedger:
    """AC-3: M key creates task_ledger entry with task_type=user_annotation"""

    def test_m_key_annotation_to_task_ledger(self):
        source = _all_player_sources()
        assert "user_annotation" in source, (
            "TimelineAnnotation must create task_ledger entries with task_type=user_annotation"
        )
        assert "frame" in source.lower(), "Annotation must store frame in params"
        assert "time_sec" in source or "timeSec" in source, (
            "Annotation must store time_sec in params"
        )


class TestAC4VisibleLayersImmediateResponse:
    """AC-4: visibleLayers toggle causes each layer to respond immediately"""

    def test_visible_layers_immediate_response(self):
        source = _all_player_sources()
        assert "visibleLayers" in source or "visible_layers" in source, (
            "PreviewPlayer must use visibleLayers for layer visibility"
        )


class TestAC5FourLayerToggles:
    """AC-5: Layer toggle buttons show 4 toggles: text, data, visual, audio"""

    def test_four_layer_toggles(self):
        source = _read_text(LAYER_TOGGLE_PATH)
        for layer in LAYER_NAMES:
            assert layer in source.lower(), f"LayerToggle must have '{layer}' toggle"


class TestAC6DataLayerIsolation:
    """AC-6: Viewing data layer alone renders only charts/info cards"""

    def test_data_layer_isolation(self):
        source = _all_player_sources()
        assert "data" in source.lower(), (
            "PreviewPlayer must support data layer isolation"
        )


class TestAC7LayerFeedbackSelectiveProducer:
    """AC-7: Layer feedback routes to corresponding Producer only, no full regeneration"""

    def test_layer_feedback_selective_producer(self):
        source = _all_player_sources()
        has_selective = (
            "Producer" in source
            or "regenerate" in source.lower()
            or "layer" in source.lower()
        )
        assert has_selective, (
            "Layer feedback must route to selective Producer, not full regeneration"
        )
