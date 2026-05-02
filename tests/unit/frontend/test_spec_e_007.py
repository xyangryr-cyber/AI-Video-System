"""Tests for [SPEC-E-007] Artifact 3-State Status Badge."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"
TEST_FILE = "components/ArtifactStatusBadge.test.tsx"


def _vitest(pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, TEST_FILE],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1OkStatusHiddenOrGreen:
    """AC-1: Badge renders nothing (or green) for `artifact_status=ok`"""

    def test_ok_status_hidden_or_green(self):
        r = _vitest("AC-1 renders nothing")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2DamagedShowsRedBadge:
    """AC-2: Badge renders red with "damaged" label/tooltip for `artifact_status=damaged`"""

    def test_damaged_shows_red_badge(self):
        r = _vitest("AC-2 renders red badge")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3MissingShowsRedBadge:
    """AC-3: Badge renders red with "missing" label/tooltip for `artifact_status=missing`"""

    def test_missing_shows_red_badge(self):
        r = _vitest("AC-3 renders red badge")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4IntegratedInPhaseNav:
    """AC-4: Badge is integrated into phase navigation items"""

    def test_integrated_in_phase_nav(self):
        r = _vitest("AC-4 badge appears")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5UpdatesOnStateRefresh:
    """AC-5: Badge updates when ProjectState refreshes (via state recovery or WebSocket)"""

    def test_updates_on_state_refresh(self):
        r = _vitest("AC-5 badge reflects")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
