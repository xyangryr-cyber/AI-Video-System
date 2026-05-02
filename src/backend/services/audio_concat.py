"""Lossless audio concat via ffmpeg concat demuxer ([SPEC-C-016]).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-1.

Wraps ``ffmpeg -f concat -safe 0 -i list.txt -c copy`` -- the canonical
lossless concatenation path for same-codec segments. ``-c copy`` avoids
re-encoding so decoded PCM of the output equals decoded PCM of the
inputs concatenated.
"""

from __future__ import annotations

import shutil
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path


class AudioConcatError(RuntimeError):
    """Raised when ffmpeg concat fails (non-zero exit)."""


def _ffmpeg_bin() -> str:
    found = shutil.which("ffmpeg")
    if not found:
        raise AudioConcatError("ffmpeg binary not found on PATH")
    return found


def concat_losslessly(
    segments: Sequence[Path],
    out_path: Path,
) -> None:
    """Concatenate ``segments`` into ``out_path`` without re-encoding.

    All segments MUST share the same codec / sample-rate / channel count;
    otherwise ffmpeg concat demuxer refuses the copy. ``out_path`` is
    overwritten if it exists.
    """
    if not segments:
        raise AudioConcatError("segments is empty")

    ffmpeg = _ffmpeg_bin()
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False, encoding="utf-8") as listf:
        for seg in segments:
            seg = Path(seg).resolve()
            # concat demuxer "file '...'" syntax; escape single quotes.
            escaped = str(seg).replace("'", r"'\''")
            listf.write(f"file '{escaped}'\n")
        listfile = Path(listf.name)

    try:
        cmd = [
            ffmpeg,
            "-y",
            "-v",
            "error",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(listfile),
            "-c",
            "copy",
            # Strip muxer-side additions so the output is byte-identical
            # to the raw-cat of the inputs -- required by the AC-1
            # "PCM diff = 0 (无损)" contract on MP3 streams.
            "-map_metadata",
            "-1",
            "-write_xing",
            "0",
            "-id3v2_version",
            "0",
            str(out_path),
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise AudioConcatError(
                f"ffmpeg concat failed (rc={proc.returncode}): {proc.stderr.strip()}"
            )
    finally:
        listfile.unlink(missing_ok=True)


__all__ = ["AudioConcatError", "concat_losslessly"]
