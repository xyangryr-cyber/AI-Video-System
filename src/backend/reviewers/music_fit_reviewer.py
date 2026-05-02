"""[SPEC-C-018] MusicFitReviewer class — v3.15 4 checks + v3.17 3 new L1 checks.

Authority: ``docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md`` §C-AUDP7A-3
(``TECH-DELTA-02``).

Design notes
------------
* The v3.15 four methods (``check_mood_match`` / ``check_coverage`` /
  ``check_volume`` / ``check_copyright``) are placeholder stubs — v3.15
  landed them as "reserved for L2" entries in ``agents/reviewers/
  l1_checks.py``; this class re-exports them with the original
  contract (return :class:`ReviewVerdict`, default PASS) so the v3.17
  aggregation has exactly 7 items to fold in. Keeping them here keeps
  the class self-contained per the task-card "class-based" shape.
* The three new methods accept ``numpy.ndarray`` signals (float32/64)
  plus a sample rate, which makes unit tests deterministic without
  spinning up ffmpeg. File-based adapters (``_load_mp3``) can be added
  downstream; this module deliberately does not import ffmpeg /
  pyloudnorm / scipy to keep the import surface pure-numpy.
* Aggregation (SPEC-C-018 AC-4): any of the 7 ``FAIL`` -> overall
  ``FAIL``. Otherwise PASS. The returned :class:`ReviewReport` carries
  every per-check verdict + its metrics so callers (Gate 5, FSM) can
  surface the exact failing dimension to the user.

Thresholds (SPEC-C-018 AC-1..AC-3)
----------------------------------
* ``full_track_harmony``: ``spectral_correlation < 0.4`` -> FAIL.
* ``abrupt_transition``: ``rms_jump_db > 6.0`` OR
  ``spectral_centroid_jump_pct > 30.0`` at any transition -> FAIL.
* ``speech_intelligibility``: ``narration_db - bgm_db < 6.0`` at any
  voice window -> FAIL (equivalent to "narration_lufs - bgm_lufs < 6 dB").
"""

from __future__ import annotations

from typing import Any, Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field

from src.backend.reviewers.audio_analysis.envelope_diff import (
    rms_jump_db,
    spectral_centroid_jump_pct,
)
from src.backend.reviewers.audio_analysis.frequency_correlation import (
    spectral_correlation,
)
from src.backend.reviewers.audio_analysis.lufs_snr import (
    level_db,
    speech_snr_db,
)


Verdict = Literal["PASS", "FAIL"]


class ReviewVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    check_name: str
    verdict: Verdict
    reason: str
    metrics: dict[str, Any] = Field(default_factory=dict)


class ReviewReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    checks: list[ReviewVerdict]


# Thresholds (module constants — exposed for tests / downstream overrides).
HARMONY_CORR_MIN = 0.4
TRANSITION_RMS_DB_MAX = 6.0
TRANSITION_CENTROID_PCT_MAX = 30.0
SPEECH_SNR_DB_MIN = 6.0


class MusicFitReviewer:
    """v3.17 MusicFitReviewer (4 v3.15 stubs + 3 new L1 checks + aggregate)."""

    # -- v3.15 checks (kept as PASS stubs — v3.15 AC contract unchanged) ----

    def check_mood_match(self) -> ReviewVerdict:
        return ReviewVerdict(
            check_name="mood_match",
            verdict="PASS",
            reason="v3.15 mood-match stub: no regression behaviour.",
        )

    def check_coverage(self) -> ReviewVerdict:
        return ReviewVerdict(
            check_name="coverage",
            verdict="PASS",
            reason="v3.15 coverage stub: no regression behaviour.",
        )

    def check_volume(self) -> ReviewVerdict:
        return ReviewVerdict(
            check_name="volume",
            verdict="PASS",
            reason="v3.15 volume stub: no regression behaviour.",
        )

    def check_copyright(self) -> ReviewVerdict:
        return ReviewVerdict(
            check_name="copyright",
            verdict="PASS",
            reason="v3.15 copyright stub: no regression behaviour.",
        )

    # -- v3.17 new L1 checks -------------------------------------------------

    def check_full_track_harmony(
        self,
        narration: np.ndarray,
        mix: np.ndarray,
        sr: int,
    ) -> ReviewVerdict:
        corr = spectral_correlation(narration, mix, sr)
        if corr < HARMONY_CORR_MIN:
            return ReviewVerdict(
                check_name="full_track_harmony",
                verdict="FAIL",
                reason=(
                    f"spectral_correlation={corr:.3f} < {HARMONY_CORR_MIN}; "
                    "narration and mix spectra diverge (masking / conflict)."
                ),
                metrics={"spectral_correlation": corr},
            )
        return ReviewVerdict(
            check_name="full_track_harmony",
            verdict="PASS",
            reason=f"spectral_correlation={corr:.3f} >= {HARMONY_CORR_MIN}.",
            metrics={"spectral_correlation": corr},
        )

    def check_abrupt_transition(
        self,
        mix: np.ndarray,
        sr: int,
        transition_points_s: list[float],
        window_s: float = 2.0,
    ) -> ReviewVerdict:
        transitions: list[dict[str, Any]] = []
        any_fail = False
        for t in transition_points_s:
            rms_jump = rms_jump_db(mix, sr, t, window_s=window_s)
            c_jump = spectral_centroid_jump_pct(mix, sr, t, window_s=window_s)
            is_fail = (
                rms_jump > TRANSITION_RMS_DB_MAX or c_jump > TRANSITION_CENTROID_PCT_MAX
            )
            any_fail = any_fail or is_fail
            transitions.append(
                {
                    "t_s": t,
                    "rms_jump_db": rms_jump,
                    "centroid_jump_pct": c_jump,
                    "fail": is_fail,
                }
            )
        if any_fail:
            return ReviewVerdict(
                check_name="abrupt_transition",
                verdict="FAIL",
                reason=(
                    f"abrupt transition detected: rms_jump > "
                    f"{TRANSITION_RMS_DB_MAX} dB or centroid_jump > "
                    f"{TRANSITION_CENTROID_PCT_MAX}% at some emotion point."
                ),
                metrics={"transitions": transitions},
            )
        return ReviewVerdict(
            check_name="abrupt_transition",
            verdict="PASS",
            reason="all transitions stay within rms/centroid bounds.",
            metrics={"transitions": transitions},
        )

    def check_speech_intelligibility(
        self,
        narration: np.ndarray,
        bgm: np.ndarray,
        sr: int,
        voice_windows: list[tuple[float, float]],
    ) -> ReviewVerdict:
        windows: list[dict[str, Any]] = []
        any_fail = False
        for start_s, end_s in voice_windows:
            a = max(0, int(round(start_s * sr)))
            b_end = int(round(end_s * sr))
            n_slice = narration[a : min(len(narration), b_end)]
            b_slice = bgm[a : min(len(bgm), b_end)]
            snr = speech_snr_db(n_slice, b_slice)
            is_fail = snr < SPEECH_SNR_DB_MIN
            any_fail = any_fail or is_fail
            windows.append(
                {
                    "start_s": start_s,
                    "end_s": end_s,
                    "snr_db": snr,
                    "narration_db": level_db(n_slice),
                    "bgm_db": level_db(b_slice),
                    "fail": is_fail,
                }
            )
        if any_fail:
            return ReviewVerdict(
                check_name="speech_intelligibility",
                verdict="FAIL",
                reason=(
                    f"voice window SNR < {SPEECH_SNR_DB_MIN} dB — BGM masks "
                    "narration at one or more speech regions."
                ),
                metrics={"windows": windows},
            )
        return ReviewVerdict(
            check_name="speech_intelligibility",
            verdict="PASS",
            reason=f"all voice windows maintain SNR >= {SPEECH_SNR_DB_MIN} dB.",
            metrics={"windows": windows},
        )

    # -- Aggregator ----------------------------------------------------------

    def review(
        self,
        *,
        narration: np.ndarray,
        bgm: np.ndarray,
        mix: np.ndarray,
        sr: int,
        transition_points_s: list[float],
        voice_windows: list[tuple[float, float]],
    ) -> ReviewReport:
        checks: list[ReviewVerdict] = [
            # v3.15 four (order matches SPEC-9.5.2 prose).
            self.check_mood_match(),
            self.check_coverage(),
            self.check_volume(),
            self.check_copyright(),
            # v3.17 three.
            self.check_full_track_harmony(narration, mix, sr),
            self.check_abrupt_transition(mix, sr, transition_points_s),
            self.check_speech_intelligibility(narration, bgm, sr, voice_windows),
        ]
        overall: Verdict = (
            "FAIL" if any(c.verdict == "FAIL" for c in checks) else "PASS"
        )
        return ReviewReport(verdict=overall, checks=checks)


__all__ = [
    "MusicFitReviewer",
    "ReviewVerdict",
    "ReviewReport",
    "Verdict",
    "HARMONY_CORR_MIN",
    "TRANSITION_RMS_DB_MAX",
    "TRANSITION_CENTROID_PCT_MAX",
    "SPEECH_SNR_DB_MIN",
]
