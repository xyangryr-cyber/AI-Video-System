"""[SPEC-C-020] SfxMixReviewer — L1 programmatic + L2 LLM fallback for
the per-segment sfx_mix_segments artifact.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-5.

Three L1 checks:

* ``check_clipping`` — any sample with ``|x| >= CLIP_PEAK_THRESHOLD``
  (0.99) fails; typical mastered signals stay below.
* ``check_speech_snr`` — ``narration_level_db - bgm_level_db`` must be
  ≥ ``SPEECH_SNR_DB_MIN`` (-6 dB per SPEC-9.6.2 v3.17 AC-2).
* ``check_bgm_synergy`` — spectral-magnitude Pearson correlation between
  the segment and the BGM track must be ≥ ``SYNERGY_CORR_MIN`` (0.3);
  near-orthogonal spectra (e.g. 9 kHz sine vs 440 Hz sine) fail.

L2 fallback (``llm_review``) is an injectable callable so tests can stub
it without touching any LLM transport. It is invoked by ``review()``
only when all three L1 checks pass, mirroring
:class:`src.backend.agents.reviewer_agent.HybridReviewer` gating so the
token budget is zero on L1 failure.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np

from src.backend.reviewers.audio_analysis.frequency_correlation import (
    spectral_correlation,
)
from src.backend.reviewers.audio_analysis.lufs_snr import speech_snr_db
from src.backend.reviewers.music_fit_reviewer import (
    ReviewReport,
    ReviewVerdict,
    Verdict,
)

CLIP_PEAK_THRESHOLD = 0.99
SPEECH_SNR_DB_MIN = -6.0
SYNERGY_CORR_MIN = 0.3


LlmReviewCallable = Callable[[np.ndarray, Any], ReviewVerdict]


def _default_llm_review(segment_audio: np.ndarray, layout_context: Any) -> ReviewVerdict:
    """No-op L2 stub used when a real LLM judge is not wired.

    Returns ``PASS`` so the 3-check L1 verdict determines the final
    outcome; real deployments inject a Claude-backed callable here.
    """
    del segment_audio, layout_context  # unused placeholder contract
    return ReviewVerdict(
        check_name="llm_review",
        verdict="PASS",
        reason="default L2 stub: no LLM judge wired; PASS by default.",
    )


class SfxMixReviewer:
    """L1 (programmatic) + L2 (LLM fallback) Reviewer for sfx mix segments."""

    def __init__(self, llm_review: LlmReviewCallable | None = None) -> None:
        self._llm_review = llm_review or _default_llm_review

    def check_clipping(self, segment_audio: np.ndarray) -> ReviewVerdict:
        if segment_audio.size == 0:
            return ReviewVerdict(
                check_name="clipping",
                verdict="PASS",
                reason="empty segment; clipping check skipped.",
                metrics={"peak_abs": 0.0, "clipped_samples": 0},
            )
        peak = float(np.max(np.abs(segment_audio)))
        clipped = int(np.sum(np.abs(segment_audio) >= CLIP_PEAK_THRESHOLD))
        metrics: dict[str, Any] = {
            "peak_abs": peak,
            "clipped_samples": clipped,
        }
        if peak >= CLIP_PEAK_THRESHOLD:
            return ReviewVerdict(
                check_name="clipping",
                verdict="FAIL",
                reason=(
                    f"peak_abs={peak:.4f} >= {CLIP_PEAK_THRESHOLD}; {clipped} clipped sample(s)."
                ),
                metrics=metrics,
            )
        return ReviewVerdict(
            check_name="clipping",
            verdict="PASS",
            reason=f"peak_abs={peak:.4f} < {CLIP_PEAK_THRESHOLD}.",
            metrics=metrics,
        )

    def check_speech_snr(
        self,
        narration: np.ndarray,
        bgm: np.ndarray,
    ) -> ReviewVerdict:
        snr = speech_snr_db(narration, bgm)
        metrics: dict[str, Any] = {"snr_db": snr}
        if snr < SPEECH_SNR_DB_MIN:
            return ReviewVerdict(
                check_name="speech_snr",
                verdict="FAIL",
                reason=(
                    f"speech_snr={snr:.2f} dB < {SPEECH_SNR_DB_MIN} dB; BGM/SFX masks narration."
                ),
                metrics=metrics,
            )
        return ReviewVerdict(
            check_name="speech_snr",
            verdict="PASS",
            reason=f"speech_snr={snr:.2f} dB >= {SPEECH_SNR_DB_MIN} dB.",
            metrics=metrics,
        )

    def check_bgm_synergy(
        self,
        segment_audio: np.ndarray,
        bgm: np.ndarray,
        sr: int,
    ) -> ReviewVerdict:
        corr = spectral_correlation(segment_audio, bgm, sr)
        metrics: dict[str, Any] = {"spectral_correlation": corr}
        if corr < SYNERGY_CORR_MIN:
            return ReviewVerdict(
                check_name="bgm_synergy",
                verdict="FAIL",
                reason=(
                    f"bgm synergy correlation={corr:.3f} < "
                    f"{SYNERGY_CORR_MIN}; spectra nearly orthogonal."
                ),
                metrics=metrics,
            )
        return ReviewVerdict(
            check_name="bgm_synergy",
            verdict="PASS",
            reason=(f"bgm synergy correlation={corr:.3f} >= {SYNERGY_CORR_MIN}."),
            metrics=metrics,
        )

    def llm_review(
        self,
        segment_audio: np.ndarray,
        layout_context: Any,
    ) -> ReviewVerdict:
        return self._llm_review(segment_audio, layout_context)

    def review(
        self,
        *,
        segment_audio: np.ndarray,
        narration: np.ndarray,
        bgm: np.ndarray,
        sr: int,
        layout_context: Any = None,
    ) -> ReviewReport:
        l1_checks: list[ReviewVerdict] = [
            self.check_clipping(segment_audio),
            self.check_speech_snr(narration, bgm),
            self.check_bgm_synergy(segment_audio, bgm, sr),
        ]
        if any(c.verdict == "FAIL" for c in l1_checks):
            return ReviewReport(verdict="FAIL", checks=l1_checks)
        l2 = self.llm_review(segment_audio, layout_context)
        verdict: Verdict = "FAIL" if l2.verdict == "FAIL" else "PASS"
        return ReviewReport(verdict=verdict, checks=[*l1_checks, l2])


__all__ = [
    "CLIP_PEAK_THRESHOLD",
    "LlmReviewCallable",
    "SPEECH_SNR_DB_MIN",
    "SYNERGY_CORR_MIN",
    "SfxMixReviewer",
]
