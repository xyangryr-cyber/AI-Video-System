"""Tests for [SPEC-E-005] Phase Artifact Preview Components (P0-P11)."""

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


class TestAC1RouterRendersCorrectComponent:
    """AC-1: PhasePreviewRouter renders the correct component for each of 12 phases (P0-P11)"""

    def test_routes_to_correct_component_for_each_phase(self):
        r = _vitest("previews/PhasePreviewRouter.test.tsx", "AC-1")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2ComponentsAcceptSpecProps:
    """AC-2: Each component accepts and renders props matching SPEC-2.6 contract table"""

    def test_components_accept_spec_props(self):
        r = _vitest("previews/PhasePreviewRouter.test.tsx", "AC-2")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3P4PerSegmentPlayPause:
    """AC-3: P4 segmented audio player supports per-segment play/pause controls"""

    def test_per_segment_play_pause(self):
        r = _vitest("previews/P4SegmentAudioPlayer.test.tsx", "AC-3")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4P8ClickToZoom:
    """AC-4: P8 grid gallery supports click-to-zoom (modal or lightbox overlay)"""

    def test_click_to_zoom(self):
        r = _vitest("previews/P8FrameGallery.test.tsx", "AC-4")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5P11PlayerCoversDownload:
    """AC-5: P11 renders embedded player + cover images + functional download button"""

    def test_player_covers_download(self):
        r = _vitest("previews/P11FinalPlayer.test.tsx", "AC-5")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6EmptyDataGraceful:
    """AC-6: Components handle empty/missing data gracefully (empty state, not crash)"""

    def test_empty_data_graceful(self):
        r = _vitest("previews/PhasePreviewRouter.test.tsx", "AC-6")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
