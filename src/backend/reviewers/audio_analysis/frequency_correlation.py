"""[SPEC-C-018] Spectral correlation helper (full_track_harmony check)."""

from __future__ import annotations

import numpy as np

_EPS = 1e-10


def spectral_correlation(
    x: np.ndarray,
    y: np.ndarray,
    sr: int,
    n_fft: int = 4096,
) -> float:
    """Pearson correlation of magnitude FFT spectra of ``x`` and ``y``.

    Uses raw (not log) magnitude. Log-magnitude was tried first but
    amplified numerical noise: for a clean tonal signal, ~99 % of bins
    sit near FFT round-off, and ``log(mag + eps)`` pushes them to a
    noisy ~-23 floor that then dominates the dot product, collapsing
    "narration + quiet noise" (which ear-intuitively correlates ~1 with
    narration) to ~0.001. Raw magnitudes give the correct answer.

    ``x`` / ``y`` may differ in length; both are zero-padded to the same
    FFT size (max of the two and ``n_fft``). Silent inputs produce a
    correlation of 0.0 rather than NaN. Result is clamped to [-1.0, 1.0]
    against floating-point drift.
    """
    n = max(len(x), len(y), n_fft)
    xf = np.abs(np.fft.rfft(x, n=n))
    yf = np.abs(np.fft.rfft(y, n=n))
    if xf.sum() < _EPS or yf.sum() < _EPS:
        return 0.0
    xc = xf - xf.mean()
    yc = yf - yf.mean()
    denom = float(np.sqrt((xc * xc).sum() * (yc * yc).sum()))
    if denom < _EPS:
        return 0.0
    corr = float((xc * yc).sum() / denom)
    return max(-1.0, min(1.0, corr))
