"""[SPEC-C-012] Five deterministic (non-LLM) Producer sub-steps.

All functions are pure: same input always produces same output.
Verified by 10-run hash comparison.
"""

from __future__ import annotations

import re
from typing import Any


def compute_word_count(text: str) -> int:
    """Count words in text. CJK characters count individually; Latin words
    are split on whitespace."""
    if not text or not text.strip():
        return 0
    cjk_chars = len(re.findall(r"[一-鿿㐀-䶿]", text))
    latin_words = len(re.findall(r"[a-zA-Z0-9]+", text))
    return cjk_chars + latin_words


def compute_ssml(text: str, *, rate: float = 1.0, emotion: str = "neutral") -> str:
    """Build SSML markup wrapping *text* with prosody and emotion tags."""
    rate_percent = f"{int(rate * 100)}%"
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis"',
        '       xml:lang="zh-CN">',
        f'  <prosody rate="{rate_percent}">',
        f'    <amazon:effect name="{emotion}">',
        f"      {text}",
        "    </amazon:effect>",
        "  </prosody>",
        "</speak>",
    ]
    return "\n".join(parts)


def compute_bgm_envelope(
    segments: list[dict[str, Any]], *, total_duration_sec: float
) -> list[dict[str, Any]]:
    """Compute BGM volume envelope points.

    Returns a list of {time_sec, volume} dicts. Fade in over first 2s,
    sustain at 0.3, duck to 0.1 during narration segments, fade out over
    last 2s.
    """
    envelope: list[dict[str, Any]] = []
    if total_duration_sec <= 0 or not segments:
        return envelope
    fade_duration = min(2.0, total_duration_sec * 0.1)
    sustain_volume = 0.3
    duck_volume = 0.1

    # Fade in (0 -> sustain)
    steps = 4
    for i in range(steps + 1):
        t = fade_duration * i / steps
        v = sustain_volume * i / steps
        envelope.append({"time_sec": round(t, 2), "volume": round(v, 3)})

    # For each segment, add envelope points
    for seg in segments:
        seg_start = float(seg.get("start_sec", 0))
        seg_end = float(seg.get("end_sec", 0))
        # Duck during narration
        mid = (seg_start + seg_end) / 2
        if seg_start > fade_duration:
            envelope.append({"time_sec": round(seg_start, 2), "volume": duck_volume})
        envelope.append({"time_sec": round(mid, 2), "volume": duck_volume})
        if seg_end < total_duration_sec - fade_duration:
            envelope.append({"time_sec": round(seg_end, 2), "volume": sustain_volume})

    # Fade out (sustain -> 0)
    for i in range(steps + 1):
        t = total_duration_sec - fade_duration + fade_duration * i / steps
        if t > (envelope[-1]["time_sec"] if envelope else 0):
            v = sustain_volume * (1 - i / steps)
            envelope.append({"time_sec": round(t, 2), "volume": round(v, 3)})

    # Sort by time
    envelope.sort(key=lambda p: p["time_sec"])
    # Remove duplicates at same time
    deduped: list[dict[str, Any]] = []
    for pt in envelope:
        if deduped and deduped[-1]["time_sec"] == pt["time_sec"]:
            deduped[-1] = pt
        else:
            deduped.append(pt)
    return deduped


def compute_sfx_timeline(segments: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Compute SFX timeline from segments.

    Returns a list of {time_sec, sfx_type, segment_id} dicts.
    Each segment transition gets a subtle whoosh marker.
    """
    if not segments:
        return []
    events: list[dict[str, Any]] = []
    for i, seg in enumerate(segments):
        seg_start = float(seg.get("start_sec", 0))
        # Start of each segment: transition sfx
        sfx_type = "whoosh_in" if i > 0 else "intro"
        events.append(
            {
                "time_sec": round(seg_start, 2),
                "sfx_type": sfx_type,
                "segment_id": seg.get("segment_id", f"seg_{i}"),
                "duration_ms": 300,
            }
        )
    return events


def compute_roughcut_params(
    segments: list[dict[str, Any]], *, fps: int = 30
) -> dict[str, Any]:
    """Compute RoughCut parameters including clip boundaries.

    Returns dict with 'clips' (one per segment with frame in/out),
    'total_frames', and 'fps'.
    """
    clips = []
    total_frames = 0
    for seg in segments:
        start_sec = float(seg.get("start_sec", 0))
        end_sec = float(seg.get("end_sec", 0))
        duration_sec = end_sec - start_sec
        frames = max(1, round(duration_sec * fps))
        clip = {
            "segment_id": seg.get("segment_id", ""),
            "frame_in": total_frames,
            "frame_out": total_frames + frames,
            "duration_sec": round(duration_sec, 2),
            "frames": frames,
        }
        clips.append(clip)
        total_frames += frames
    return {
        "clips": clips,
        "total_frames": total_frames,
        "fps": fps,
    }


__all__ = [
    "compute_bgm_envelope",
    "compute_roughcut_params",
    "compute_sfx_timeline",
    "compute_ssml",
    "compute_word_count",
]
