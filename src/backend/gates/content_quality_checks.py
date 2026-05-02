"""[SPEC-D-012] Content quality detectors for GateKeeper.

Three detection functions for content-level gate checks:
- detect_placeholder_text: find templated placeholder strings in text artifacts
- detect_uniform_color_frame: detect solid-color image frames (PIL + numpy)
- detect_duration_deviation: flag >10 percent deviation between declared and measured duration
"""

from __future__ import annotations

import re

import numpy as np


# Regex patterns for placeholder text in P0-P3 artifacts.
_PLACEHOLDER_PATTERNS: list[str] = [
    r"Key point \d+ for \w+",
    r"\w+ data point \d+",
    r"第\d+部分.*Key point",
    r"Transition from \w+ to \w+",
]


def detect_placeholder_text(artifact: dict) -> list[str]:
    """Scan artifact text content for known placeholder patterns.

    Args:
        artifact: dict optionally containing ``"text"`` or ``"content"`` key.

    Returns:
        List of matched placeholder strings (empty if none found).
    """
    text: str = artifact.get("text", "") or artifact.get("content", "") or ""
    if not text:
        return []

    found: list[str] = []
    for pattern in _PLACEHOLDER_PATTERNS:
        matches = re.findall(pattern, text)
        found.extend(matches)
    return found


def detect_uniform_color_frame(image_path: str) -> bool:
    """Check whether an image frame is a uniform / solid color.

    Opens the image with PIL, converts to a numpy array, and computes the
    pixel-value standard deviation.  std < 10 indicates a solid-color frame.

    Args:
        image_path: Absolute or relative path to the image file.

    Returns:
        True if the image appears to be a solid color frame.
    """
    from PIL import Image

    img = Image.open(image_path)
    arr = np.array(img)

    if len(arr.shape) == 3:
        std_val = float(np.std(arr))
    elif len(arr.shape) == 2:
        std_val = float(np.std(arr))
    else:
        # Unexpected shape — not a solid color by default.
        return False

    return std_val < 10.0


def detect_duration_deviation(
    artifact: dict, measured_sec: float
) -> tuple[bool, float]:
    """Compare the artifact's declared duration against the measured value.

    Deviation > 10 percent of the declared value is flagged.

    Args:
        artifact: dict with ``"duration"`` key (seconds, numeric).
        measured_sec: Actual measured duration in seconds.

    Returns:
        Tuple of (is_deviation_excessive, deviation_percent).
        If declared duration is zero the check returns ``(False, 0.0)``.
    """
    declared: float = float(
        artifact.get("duration", 0) or artifact.get("declared_duration", 0) or 0
    )
    if declared == 0.0:
        return (False, 0.0)

    deviation_pct: float = abs(declared - measured_sec) / declared * 100.0
    is_deviation: bool = deviation_pct > 10.0
    return (is_deviation, round(deviation_pct, 1))
