"""Tests for [SPEC-E-001] Project List Page (pytest wraps vitest)."""

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


class TestAC4MultipleProjectsDifferentPhases:
    def test_multiple_projects_different_phases(self):
        r = _vitest("pages/ProjectList.test.tsx", "AC-4 renders fixture")
        assert r.returncode == 0, r.stdout + r.stderr


class TestAC5UpdatedAtRefreshesOnWsEvent:
    def test_updated_at_refreshes_on_ws_event(self):
        r = _vitest("hooks/useProjects.test.tsx", "AC-5:")
        assert r.returncode == 0, r.stdout + r.stderr
