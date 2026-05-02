"""Tests for [SPEC-E-009] Error State UX (3-Tier Classification + ERROR_UX_MAP)."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"
MAP_FILE = "utils/errorUxMap.test.ts"
COMPONENTS_DIR = "components/errors"


def _vitest_map(pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, MAP_FILE],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _vitest_components(pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, COMPONENTS_DIR],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1MapsAll8ErrorCodes:
    """AC-1: ERROR_UX_MAP maps all 8 error codes (EVID_3002, EVID_3004, EVID_4001, EVID_4002, EVID_2001, EVID_5001, EVID_5002, EVID_3001) to tier + component + recovery actions"""

    def test_maps_all_8_error_codes(self):
        r = _vitest_map("AC-1 maps all 8 error codes")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2NoLlmCallsInMap:
    """AC-2: ERROR_UX_MAP contains zero LLM calls -- pure static lookup"""

    def test_no_llm_calls_in_map(self):
        r = _vitest_map("AC-2 is pure static")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3AutoHandlingToastNonBlocking:
    """AC-3: auto_handling errors (EVID_3002, EVID_3004) render non-blocking toast with ETA, do not obscure main UI"""

    def test_auto_handling_toast_non_blocking(self):
        r = _vitest_map("AC-3 EVID_3002")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4UserChoiceModalWithButtons:
    """AC-4: user_choice errors (EVID_4001, EVID_4002, EVID_2001) render modal with >= 2 action buttons"""

    def test_user_choice_modal_with_buttons(self):
        r = _vitest_map("AC-4 user_choice entries")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5UserActionModalExpandableDetails:
    """AC-5: user_action errors (EVID_5001, EVID_5002, EVID_3001) render modal with expandable technical details section"""

    def test_user_action_modal_expandable_details(self):
        r = _vitest_components("renders expandable technical details")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6EachCodeHasRecoveryAction:
    """AC-6: Each error code in the map has at least one associated recovery action"""

    def test_each_code_has_recovery_action(self):
        r = _vitest_map("AC-6 every code has")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC7UnknownCodeFallback:
    """AC-7: Unknown error codes fall back to user_action tier with generic modal"""

    def test_unknown_code_fallback(self):
        r = _vitest_map("AC-7 unknown code")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
