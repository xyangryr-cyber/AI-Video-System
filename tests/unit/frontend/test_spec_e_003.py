"""Tests for [SPEC-E-003] State Recovery on Page Load (pytest wraps vitest)."""

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


class TestAC1FetchesProjectStateOnLoad:
    """AC-1: Page load calls GET /projects/{id}/state and renders all ProjectState fields"""

    def test_fetches_project_state_on_mount(self):
        r = _vitest("hooks/useProjectState.test.tsx", "AC-1")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2NoUndefinedFieldsInState:
    """AC-2: No field in the rendered state is undefined (verified against ProjectState interface)"""

    def test_no_undefined_fields_in_state(self):
        r = _vitest("hooks/useProjectState.test.tsx", "AC-2")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3PhaseNavHighlightsCurrentPhase:
    """AC-3: Phase navigation highlights current_phase from restored state"""

    def test_phase_nav_highlights_current_phase(self):
        r = _vitest("pages/WorkflowPage.test.tsx", "AC-3")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4RendersCorrectPhaseComponent:
    """AC-4: Preview area renders the correct phase-specific component based on current_phase"""

    def test_renders_correct_phase_component(self):
        r = _vitest("pages/WorkflowPage.test.tsx", "AC-4")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5ShowsLoadingDuringFetch:
    """AC-5: State recovery completes within 10s (loading indicator shown during fetch)"""

    def test_shows_loading_during_fetch(self):
        r = _vitest("pages/WorkflowPage.test.tsx", "AC-5")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6ErrorStateWithRetry:
    """AC-6: API failure renders error state with retry button"""

    def test_error_state_with_retry(self):
        r = _vitest("pages/WorkflowPage.test.tsx", "AC-6")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
