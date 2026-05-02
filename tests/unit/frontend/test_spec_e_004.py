"""Tests for [SPEC-E-004] Settings Page."""

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


class TestAC1RendersTabs:
    """AC-1: `/settings` route renders page with tabs: API Config, Models, Preferences"""

    def test_renders_four_tabs(self):
        r = _vitest("SettingsPage.test.tsx", "AC-1 renders four tabs")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2ApiConfigLoadsAndSaves:
    """AC-2: API Config tab reads from `GET /api/settings` and writes via `PUT /api/settings/model-config`"""

    def test_loads_and_saves_model_config(self):
        r = _vitest("settings/ApiConfigTab.test.tsx", "AC-2 loads model config")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

        r2 = _vitest("settings/ApiConfigTab.test.tsx", "AC-2 saves model config")
        assert r2.returncode == 0, f"stdout={r2.stdout}\nstderr={r2.stderr}"


class TestAC3PreferencesLoadsAndSaves:
    """AC-3: Preferences tab reads from `GET /api/settings/preferences` and writes via `PUT /api/settings/preferences`"""

    def test_loads_and_saves_preferences(self):
        r = _vitest("settings/PreferencesTab.test.tsx", "AC-3 loads preferences")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"

        r2 = _vitest("settings/PreferencesTab.test.tsx", "AC-3 saves preferences")
        assert r2.returncode == 0, f"stdout={r2.stdout}\nstderr={r2.stderr}"


class TestAC4BrandKitSavesViaApi:
    """AC-4: Brand Kit tab saves via `PUT /api/settings/brand-kit` (SQLite, no file write)"""

    def test_saves_brand_kit_via_api(self):
        r = _vitest("settings/BrandKitTab.test.tsx", "AC-4 saves brand kit")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
