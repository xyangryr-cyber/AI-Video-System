"""Tests for [SPEC-E-010] CandidateSelector Component."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"
HOOK_FILE = "hooks/useCandidateSelection.test.tsx"
COMPONENT_FILE = "components/CandidateSelector.test.tsx"


def _vitest_hook(pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, HOOK_FILE],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


def _vitest_component(pattern: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, COMPONENT_FILE],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1DisplaysUpTo3Candidates:
    """AC-1: Component displays up to 3 candidates with preview capability"""

    def test_displays_up_to_3_candidates(self):
        r = _vitest_component("AC-1 displays up to 3 candidates")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2StateMachineTransitions:
    """AC-2: State machine transitions: idle -> previewing -> selected -> confirmed"""

    def test_state_machine_transitions(self):
        r = _vitest_hook("AC-2 state transitions")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3TwoStepConfirmation:
    """AC-3: Two-step confirmation: user must select then explicitly confirm"""

    def test_two_step_confirmation(self):
        r = _vitest_hook("AC-3 two-step confirm")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC460sTimeoutReminderOnce:
    """AC-4: After 60s of no interaction, displays reminder toast; fires only once"""

    def test_60s_timeout_reminder_once(self):
        r = _vitest_hook("AC-4 fires reminder")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5SkipAcceptsRecommended:
    """AC-5: Skip and accept recommendation confirms is_recommended candidate"""

    def test_skip_accepts_recommended(self):
        r = _vitest_hook("AC-5 skipAndAccept")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6ConfirmCallsPreferencesApi:
    """AC-6: Confirmation calls POST /api/projects/{id}/preferences/confirm with candidate_id"""

    def test_confirm_calls_preferences_api(self):
        r = _vitest_component("AC-6 confirm posts")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC7ReusableAcrossPhases:
    """AC-7: Component is reusable across phases (accepts generic Candidate interface)"""

    def test_reusable_across_phases(self):
        r = _vitest_component("AC-7 accepts generic")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC8NoUnlockButton:
    """AC-8: style_lock unlock requires explicit action; no unlock button in CandidateSelector"""

    def test_no_unlock_button(self):
        r = _vitest_component("AC-8 no unlock")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
