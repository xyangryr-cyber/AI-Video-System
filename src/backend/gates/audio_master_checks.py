"""[SPEC-D-018] P4 audio-master L1 check utilities.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §D-AUDP7A-1.

Three reusable, side-effect-free checks shared by Gate-P4 (this task)
and the downstream renderers that will land Gate-P5/P6:

* :func:`check_master_file_exists` -- master file is on disk and
  non-empty.
* :func:`check_master_playable` -- ffprobe reports a strictly positive
  duration (callers may inject a probe for unit-test isolation).
* :func:`check_checksum_consistent` -- recomputed sha256 matches the
  artifact's advertised ``checksum`` field.

All checks return a :class:`~src.backend.engine.gatekeeper.CheckResult`
tuple so the Gate-P4 aggregator can render them alongside the SPEC-8
7-item gate without ad-hoc bool plumbing.
"""

from __future__ import annotations

import hashlib
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path

from src.backend.engine.gatekeeper import CheckResult

ProbeFn = Callable[[Path], float]


__all__ = [
    "check_master_file_exists",
    "check_master_playable",
    "check_checksum_consistent",
    "ffprobe_duration_seconds",
]


def check_master_file_exists(path: Path) -> CheckResult:
    """File exists and is non-empty."""
    p = Path(path)
    if not p.exists():
        return CheckResult("master_exists", False, f"master file not found: {p}")
    if not p.is_file():
        return CheckResult("master_exists", False, f"master path is not a file: {p}")
    try:
        size = p.stat().st_size
    except OSError as exc:
        return CheckResult("master_exists", False, f"stat failed on master file: {exc}")
    if size == 0:
        return CheckResult("master_exists", False, f"master file is empty: {p}")
    return CheckResult("master_exists", True)


def check_master_playable(path: Path, *, probe: ProbeFn | None = None) -> CheckResult:
    """ffprobe reports duration > 0 (``probe`` injectable for tests)."""
    fn = probe or ffprobe_duration_seconds
    try:
        duration = fn(Path(path))
    except Exception as exc:  # noqa: BLE001 - surface probe failure as FAIL
        return CheckResult(
            "master_playable",
            False,
            f"ffprobe failed on master: {exc}",
        )
    if duration <= 0.0:
        return CheckResult(
            "master_playable",
            False,
            f"ffprobe duration <= 0 (got {duration!r})",
        )
    return CheckResult("master_playable", True)


def check_checksum_consistent(path: Path, expected_checksum: str) -> CheckResult:
    """Recomputed sha256 of ``path`` matches ``expected_checksum``."""
    p = Path(path)
    if not p.is_file():
        return CheckResult(
            "checksum_consistent",
            False,
            f"checksum target not a file: {p}",
        )
    actual = _sha256_of_file(p)
    if actual != expected_checksum:
        return CheckResult(
            "checksum_consistent",
            False,
            (f"checksum drift: computed {actual} != declared {expected_checksum}"),
        )
    return CheckResult("checksum_consistent", True)


# ---------------------------------------------------------------------


def ffprobe_duration_seconds(path: Path) -> float:
    """Return media duration in seconds via ffprobe."""
    bin_path = shutil.which("ffprobe")
    if not bin_path:
        raise RuntimeError("ffprobe binary not found on PATH")
    out = subprocess.run(
        [
            bin_path,
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=nokey=1:noprint_wrappers=1",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    text = out.stdout.strip()
    return float(text)


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"
