"""[SPEC-C-018] LUFS-approximation SNR helper (speech_intelligibility).

We intentionally do NOT depend on pyloudnorm: the py3.13 test env is
zero-install and every SPEC-C task so far uses pure numpy. The spec's
"pyloudnorm LUFS 分窗" is interpreted as "per-window level in dB" — we
use RMS-based dBFS, which matches the spec's threshold expression
(narration level minus bgm level >= 6 dB) one-for-one. If the real
system later wants true LUFS, swap :func:`level_db` for
``pyloudnorm.Meter.integrated_loudness`` with no change to the caller.
"""

from __future__ import annotations

import numpy as np

_EPS = 1e-10


def level_db(x: np.ndarray) -> float:
    """RMS level in dB (dBFS with full scale == 1.0). Silence -> -120 dB."""
    if x.size == 0:
        return -120.0
    r = float(np.sqrt(np.mean(x.astype(np.float64) ** 2)))
    return float(20.0 * np.log10(max(r, _EPS)))


def speech_snr_db(narration_window: np.ndarray, bgm_window: np.ndarray) -> float:
    """narration_db - bgm_db for a single time window."""
    return level_db(narration_window) - level_db(bgm_window)
