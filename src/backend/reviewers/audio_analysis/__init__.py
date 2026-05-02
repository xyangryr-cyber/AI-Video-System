"""[SPEC-C-018] pure-numpy audio-analysis helpers for MusicFitReviewer v3.17.

Every function is deterministic and side-effect free; they accept numpy
arrays (float32 / float64) and return floats / dicts. No ffmpeg, no
pyloudnorm, no scipy — keeps the py3.13 test env zero-install.
"""

from src.backend.reviewers.audio_analysis.frequency_correlation import (
    spectral_correlation,
)
from src.backend.reviewers.audio_analysis.envelope_diff import (
    rms_db,
    rms_jump_db,
    spectral_centroid,
    spectral_centroid_jump_pct,
)
from src.backend.reviewers.audio_analysis.lufs_snr import (
    level_db,
    speech_snr_db,
)

__all__ = [
    "spectral_correlation",
    "rms_db",
    "rms_jump_db",
    "spectral_centroid",
    "spectral_centroid_jump_pct",
    "level_db",
    "speech_snr_db",
]
