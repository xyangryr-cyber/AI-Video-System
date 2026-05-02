"""Tests for [SPEC-C-018] MusicFitReviewer 升级 — 三项 L1 程序化检查.

All real assertions live here; `tests/unit/reviewers/test_music_fit_reviewer_v317.py`
and `tests/integration/reviewers/test_music_fit_aggregate.py` re-export the same
classes (importlib.spec_from_file_location — the ``backend-core`` folder name
has a dash and is not a valid Python identifier). Instantiating
:class:`MusicFitReviewer` inline in each test (rather than via a pytest
fixture) keeps the re-export files fixture-free.

Synthetic numpy signals replace real mp3 fixtures: every check operates on a
narration / bgm / mix ndarray triple so thresholds can be probed deterministically
without ffmpeg / pyloudnorm. File-based integration will come from SPEC-C-017's
bgm_mix_preview fixtures in later tasks.
"""

from __future__ import annotations

import numpy as np

from src.backend.reviewers.music_fit_reviewer import (
    MusicFitReviewer,
    ReviewReport,
    ReviewVerdict,
)


SR = 44100


def _tone(freq: float, duration_s: float, sr: int = SR, amp: float = 0.3) -> np.ndarray:
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def _noise(
    duration_s: float, sr: int = SR, amp: float = 0.3, seed: int = 0
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return (amp * rng.standard_normal(int(sr * duration_s))).astype(np.float32)


def _silence(duration_s: float, sr: int = SR) -> np.ndarray:
    return np.zeros(int(sr * duration_s), dtype=np.float32)


def _reviewer() -> MusicFitReviewer:
    return MusicFitReviewer()


# -----------------------------------------------------------------------
# AC-1: check_full_track_harmony
# -----------------------------------------------------------------------


class TestAC1:
    """spectral_correlation(narration, mix) >= 0.4 -> PASS; else FAIL.

    Tests use the fact that when bgm is small relative to narration, the mix's
    log-magnitude spectrum tracks narration closely (high correlation); when
    bgm dominates with a spectrally-unrelated signal, correlation drops.
    """

    def test_full_track_harmony_pass(self) -> None:
        narration = _tone(440, 3.0)
        bgm = 0.05 * _noise(3.0, seed=1)
        mix = narration + bgm
        v = _reviewer().check_full_track_harmony(narration, mix, SR)
        assert v.verdict == "PASS", v.reason
        assert v.metrics["spectral_correlation"] >= 0.4

    def test_full_track_harmony_fail(self) -> None:
        narration = _tone(440, 3.0, amp=0.01)  # tiny narration
        bgm = _noise(3.0, amp=0.8, seed=2)  # loud unrelated noise
        mix = narration + bgm
        v = _reviewer().check_full_track_harmony(narration, mix, SR)
        assert v.verdict == "FAIL"
        assert v.metrics["spectral_correlation"] < 0.4
        assert "spectral_correlation" in v.reason


# -----------------------------------------------------------------------
# AC-2: check_abrupt_transition
# -----------------------------------------------------------------------


class TestAC2:
    """At each emotion transition, compare 2s before/after windows.

    FAIL if rms_jump > 6 dB OR spectral_centroid_jump > 30 %.
    """

    def test_abrupt_transition_pass(self) -> None:
        # 6 s mix with tiny amplitude variation across t=3 s.
        mix = 0.3 * np.concatenate(
            [_tone(440, 3.0, amp=1.0), _tone(440, 3.0, amp=1.05)]
        )
        v = _reviewer().check_abrupt_transition(mix, SR, [3.0])
        assert v.verdict == "PASS", v.reason
        assert max(p["rms_jump_db"] for p in v.metrics["transitions"]) <= 6.0

    def test_abrupt_transition_fail(self) -> None:
        # 6 s mix where amplitude jumps 10x at t=3 s (≈ 20 dB).
        before = 0.05 * _tone(440, 3.0)
        after = 0.5 * _tone(440, 3.0)
        mix = np.concatenate([before, after])
        v = _reviewer().check_abrupt_transition(mix, SR, [3.0])
        assert v.verdict == "FAIL"
        assert any(p["rms_jump_db"] > 6.0 for p in v.metrics["transitions"])


# -----------------------------------------------------------------------
# AC-3: check_speech_intelligibility
# -----------------------------------------------------------------------


class TestAC3:
    """For every voice window, narration_db - bgm_db must be >= 6 dB."""

    def test_speech_intelligibility_pass(self) -> None:
        narration = _tone(440, 3.0, amp=0.4)
        bgm = _noise(3.0, amp=0.05, seed=3)
        v = _reviewer().check_speech_intelligibility(
            narration, bgm, SR, voice_windows=[(0.5, 2.5)]
        )
        assert v.verdict == "PASS", v.reason
        assert min(w["snr_db"] for w in v.metrics["windows"]) >= 6.0

    def test_speech_intelligibility_fail(self) -> None:
        narration = _tone(440, 3.0, amp=0.1)
        bgm = _noise(3.0, amp=0.4, seed=4)
        v = _reviewer().check_speech_intelligibility(
            narration, bgm, SR, voice_windows=[(0.5, 2.5)]
        )
        assert v.verdict == "FAIL"
        assert min(w["snr_db"] for w in v.metrics["windows"]) < 6.0


# -----------------------------------------------------------------------
# AC-4: aggregate review() over 4 v3.15 + 3 v3.17 checks
# -----------------------------------------------------------------------


def _ok_inputs() -> dict:
    """All-green synthetic inputs for review()."""
    narration = _tone(440, 4.0, amp=0.4)
    bgm = _noise(4.0, amp=0.02, seed=5)
    mix = narration + bgm
    return dict(
        narration=narration,
        bgm=bgm,
        mix=mix,
        sr=SR,
        transition_points_s=[2.0],
        voice_windows=[(0.5, 3.5)],
    )


class TestAC4:
    def test_aggregate_v315_pass_v317_fail(self) -> None:
        # Force full_track_harmony to FAIL by supplying a loud unrelated bgm
        narration = _tone(440, 4.0, amp=0.01)
        bgm = _noise(4.0, amp=0.8, seed=6)
        mix = narration + bgm
        report = _reviewer().review(
            narration=narration,
            bgm=bgm,
            mix=mix,
            sr=SR,
            transition_points_s=[2.0],
            voice_windows=[(0.5, 3.5)],
        )
        assert report.verdict == "FAIL"
        failing = [c for c in report.checks if c.verdict == "FAIL"]
        assert any(c.check_name == "full_track_harmony" for c in failing)
        assert len(failing) >= 1

    def test_aggregate_all_pass(self) -> None:
        report = _reviewer().review(**_ok_inputs())
        assert report.verdict == "PASS", [c.reason for c in report.checks]
        assert all(c.verdict == "PASS" for c in report.checks)


# -----------------------------------------------------------------------
# AC-5: handmade "bad" fixtures
# -----------------------------------------------------------------------


class TestAC5:
    def test_high_bgm_fixture_fails(self) -> None:
        narration = _tone(440, 4.0, amp=0.05)
        bgm = _noise(4.0, amp=0.5, seed=7)  # BGM much louder than narration
        report = _reviewer().review(
            narration=narration,
            bgm=bgm,
            mix=narration + bgm,
            sr=SR,
            transition_points_s=[2.0],
            voice_windows=[(0.5, 3.5)],
        )
        assert report.verdict == "FAIL"
        failing_names = {c.check_name for c in report.checks if c.verdict == "FAIL"}
        assert "speech_intelligibility" in failing_names

    def test_abrupt_bgm_fixture_fails(self) -> None:
        narration = _tone(440, 6.0, amp=0.4)
        bgm_quiet = 0.01 * _noise(3.0, seed=8)
        bgm_loud = 0.5 * _noise(3.0, seed=9)
        bgm = np.concatenate([bgm_quiet, bgm_loud])  # amplitude jump at t=3 s
        mix = narration + bgm
        report = _reviewer().review(
            narration=narration,
            bgm=bgm,
            mix=mix,
            sr=SR,
            transition_points_s=[3.0],
            voice_windows=[(0.5, 5.5)],
        )
        assert report.verdict == "FAIL"
        failing_names = {c.check_name for c in report.checks if c.verdict == "FAIL"}
        assert "abrupt_transition" in failing_names


# -----------------------------------------------------------------------
# AC-6: v3.15 four existing checks do not regress
# -----------------------------------------------------------------------


class TestAC6:
    def test_v315_existing_checks_no_regression(self) -> None:
        """The 4 v3.15 stub methods must keep returning PASS with the
        original signatures (mood_match / coverage / volume / copyright)."""
        r = _reviewer()
        m = r.check_mood_match()
        c = r.check_coverage()
        v = r.check_volume()
        cp = r.check_copyright()
        for result in (m, c, v, cp):
            assert isinstance(result, ReviewVerdict)
            assert result.verdict == "PASS"


# -----------------------------------------------------------------------
# AC-7: report structure has 7 per-check verdict + reason + metric keys
# -----------------------------------------------------------------------


class TestAC7:
    def test_report_structure_seven_checks(self) -> None:
        report = _reviewer().review(**_ok_inputs())
        assert isinstance(report, ReviewReport)
        names = [c.check_name for c in report.checks]
        expected = {
            "mood_match",
            "coverage",
            "volume",
            "copyright",  # v3.15
            "full_track_harmony",
            "abrupt_transition",
            "speech_intelligibility",  # v3.17
        }
        assert set(names) == expected
        for c in report.checks:
            assert c.verdict in ("PASS", "FAIL")
            assert isinstance(c.reason, str) and c.reason
            assert isinstance(c.metrics, dict)
        # Metric keys specifically named by AC-7.
        h = next(c for c in report.checks if c.check_name == "full_track_harmony")
        assert "spectral_correlation" in h.metrics
        a = next(c for c in report.checks if c.check_name == "abrupt_transition")
        assert "transitions" in a.metrics
        s = next(c for c in report.checks if c.check_name == "speech_intelligibility")
        assert "windows" in s.metrics
