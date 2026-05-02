"""[SPEC-C-020] SfxMixReviewer unit tests (AC-2).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-5.

Each of the 3 L1 checks (clipping / speech_snr / bgm_synergy) is exercised
with one PASS example and one FAIL example. Signals are pure numpy, so
the tests do not depend on ffmpeg / pyloudnorm and run deterministically
across environments.
"""

from __future__ import annotations

import numpy as np


def _sine(sr: int, secs: float, freq: float, amp: float = 0.3) -> np.ndarray:
    t = np.arange(int(sr * secs)) / sr
    return (amp * np.sin(2 * np.pi * freq * t)).astype(np.float64)


class TestAC2Clipping:
    def test_clipping_detection(self) -> None:
        from src.backend.reviewers.sfx_mix_reviewer import SfxMixReviewer

        sr = 44100
        r = SfxMixReviewer()
        normal = _sine(sr, 0.5, 440.0, amp=0.3)
        assert r.check_clipping(normal).verdict == "PASS"

        clipped = normal.copy()
        clipped[100:200] = 1.0
        clipped[300:400] = -1.0
        assert r.check_clipping(clipped).verdict == "FAIL"


class TestAC2SpeechSnr:
    def test_speech_snr(self) -> None:
        from src.backend.reviewers.sfx_mix_reviewer import SfxMixReviewer

        sr = 44100
        r = SfxMixReviewer()
        narration = _sine(sr, 0.5, 300.0, amp=0.3)
        bgm_quiet = _sine(sr, 0.5, 120.0, amp=0.02)
        assert r.check_speech_snr(narration, bgm_quiet).verdict == "PASS"

        bgm_loud = _sine(sr, 0.5, 120.0, amp=0.9)
        assert r.check_speech_snr(narration, bgm_loud).verdict == "FAIL"


class TestAC2BgmSynergy:
    def test_bgm_synergy(self) -> None:
        from src.backend.reviewers.sfx_mix_reviewer import SfxMixReviewer

        sr = 44100
        r = SfxMixReviewer()
        bgm = _sine(sr, 1.0, 440.0, amp=0.3)
        aligned = bgm.copy()
        assert r.check_bgm_synergy(aligned, bgm, sr).verdict == "PASS"

        unrelated = _sine(sr, 1.0, 9000.0, amp=0.3)
        assert r.check_bgm_synergy(unrelated, bgm, sr).verdict == "FAIL"
