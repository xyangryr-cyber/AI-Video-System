"""[SPEC-C-018] Envelope and spectral-centroid differentials (abrupt_transition)."""

from __future__ import annotations

import numpy as np

_EPS = 1e-10


def rms_db(x: np.ndarray) -> float:
    if x.size == 0:
        return -120.0
    r = float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))
    return float(20.0 * np.log10(max(r, _EPS)))


def _window(x: np.ndarray, sr: int, start_s: float, end_s: float) -> np.ndarray:
    a = max(0, int(round(start_s * sr)))
    b = min(len(x), int(round(end_s * sr)))
    if b <= a:
        return x[0:0]
    return x[a:b]


def rms_jump_db(
    x: np.ndarray,
    sr: int,
    center_s: float,
    window_s: float = 2.0,
) -> float:
    """|RMS_dB(center-window..center) - RMS_dB(center..center+window)|."""
    before = _window(x, sr, center_s - window_s, center_s)
    after = _window(x, sr, center_s, center_s + window_s)
    return abs(rms_db(before) - rms_db(after))


def spectral_centroid(x: np.ndarray, sr: int) -> float:
    if x.size == 0:
        return 0.0
    X = np.abs(np.fft.rfft(x))
    total = float(X.sum())
    if total < _EPS:
        return 0.0
    f = np.fft.rfftfreq(len(x), 1.0 / sr)
    return float((f * X).sum() / total)


def spectral_centroid_jump_pct(
    x: np.ndarray,
    sr: int,
    center_s: float,
    window_s: float = 2.0,
) -> float:
    """(|c_before - c_after| / max(c_before, c_after)) * 100.

    Returns 0.0 when both windows are empty / silent (no jump).
    """
    before = _window(x, sr, center_s - window_s, center_s)
    after = _window(x, sr, center_s, center_s + window_s)
    cb = spectral_centroid(before, sr)
    ca = spectral_centroid(after, sr)
    denom = max(cb, ca)
    if denom < _EPS:
        return 0.0
    return abs(cb - ca) / denom * 100.0
