"""Tests for [SPEC-E-006] Data Verification Panel."""

import subprocess
from pathlib import Path

FRONTEND_ROOT = Path(__file__).parents[3] / "src" / "frontend"


def _vitest(test_file: str, pattern: str):
    return subprocess.run(
        ["pnpm", "vitest", "run", "--reporter=basic", "-t", pattern, test_file],
        cwd=FRONTEND_ROOT,
        capture_output=True,
        text=True,
        timeout=180,
    )


class TestAC1SummaryStatsBar:
    def test_summary_stats_bar(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-1:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC2RendersDataPointFields:
    def test_renders_data_point_fields(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-2:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC3LlmGeneratedShowsVerifyAndConfirm:
    def test_llm_generated_shows_verify_and_confirm(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-3:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC4StaleShowsReverify:
    def test_stale_shows_reverify(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-4:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC5VerifyTriggersSubtask:
    def test_verify_triggers_subtask(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-5:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC6ManualConfirmUpdatesTrust:
    def test_manual_confirm_updates_trust(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-6:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC7ExpandShowsNotes:
    def test_expand_shows_notes(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-7:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC8RefutedRendersRed:
    def test_refuted_renders_red(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-8:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC9WsRealtimeStatsUpdate:
    def test_ws_realtime_stats_update(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-9:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"


class TestAC10StatsConsistentWithRows:
    def test_stats_consistent_with_rows(self):
        r = _vitest("components/DataVerificationPanel.test.tsx", "AC-10:")
        assert r.returncode == 0, f"stdout={r.stdout}\nstderr={r.stderr}"
