"""[SPEC-C-017] AudioMixPreviewService -- P5 narration+BGM mix preview.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-2.

``render_preview`` takes the current ``narration_master`` + a BGM candidate
+ an ``EnvelopeSpec`` and emits ``phase_5/bgm_mix_preview_{candidate_id}.mp3``
for the P5 candidate selector. It MUST NOT touch ``projects.master_audio_ref``
(that flip is the ``BgmMixRenderer`` contract once the user confirms a
candidate). Determinism: same inputs + same ffmpeg binary => byte-identical
output file (AC-1).

Missing-precondition contract (AC-6): if the project has no
``master_audio_ref`` row or the on-disk narration master file is absent,
raise ``MasterAudioNotReadyError`` before invoking ffmpeg.
"""

from __future__ import annotations

import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import TYPE_CHECKING

from src.backend.repositories.project_state_repo import (
    ProjectStateRepository,
)
from src.backend.services.audio_envelope import EnvelopeSpec
from src.shared.schemas.audio_master import NarrationMasterArtifact
from src.shared.schemas.bgm_candidate import BgmCandidate

if TYPE_CHECKING:  # pragma: no cover - typing only
    pass


PHASE_DIR = "phase_5"


class MasterAudioNotReadyError(RuntimeError):
    """Raised when render_preview runs before the narration master is staged.

    Signals that upstream P4 (C-016) has not produced
    ``phase_4/narration_master.{mp3,json}`` AND/OR
    ``projects.master_audio_ref`` is empty or not a narration_master pointer.
    """


class AudioMixPreviewService:
    """Render ``phase_5/bgm_mix_preview_{candidate_id}.mp3``.

    Does not write the master audio artifact and does not update
    ``projects.master_audio_ref`` -- that is strictly ``BgmMixRenderer``'s
    job once a candidate is confirmed by the user.
    """

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._repo = ProjectStateRepository(conn)

    def render_preview(
        self,
        project_id: str,
        project_root: Path,
        narration_master: NarrationMasterArtifact,
        bgm_candidate: BgmCandidate,
        envelope: EnvelopeSpec,
    ) -> Path:
        """Return the absolute path to the freshly-rendered preview file."""
        _assert_narration_ready(self._repo, project_id, project_root, narration_master)

        narration_path = (project_root / narration_master.file_path).resolve()
        bgm_path = _resolve_bgm_source(project_root, bgm_candidate)
        if not bgm_path.is_file():
            raise MasterAudioNotReadyError(f"bgm candidate source not found: {bgm_path}")

        phase_dir = project_root / PHASE_DIR
        phase_dir.mkdir(parents=True, exist_ok=True)
        preview_path = phase_dir / (f"bgm_mix_preview_{bgm_candidate.candidate_id}.mp3")
        _run_mix(
            narration_path=narration_path,
            bgm_path=bgm_path,
            out_path=preview_path,
            envelope=envelope,
            narration_duration_s=narration_master.total_duration_seconds,
        )
        return preview_path


# ---- module-level helpers (shared with BgmMixRenderer) ---------------


def _assert_narration_ready(
    repo: ProjectStateRepository,
    project_id: str,
    project_root: Path,
    narration_master: NarrationMasterArtifact,
) -> None:
    """Validate P4 narration master is produced and on-disk.

    Gate semantics: P5 mix services can run once the narration master has
    been materialised on disk. We do not pin ``projects.master_audio_ref``
    to ``narration_master`` because ``BgmMixRenderer`` itself flips the
    ref to ``bgm_mix_master`` on success; a subsequent preview re-render
    (different candidate) must still be able to run against the unchanged
    narration file on disk.
    """
    try:
        ref = repo.get_master_audio_ref(project_id)
    except KeyError as exc:
        raise MasterAudioNotReadyError(f"project {project_id!r} not found") from exc
    if ref is None:
        raise MasterAudioNotReadyError(
            "projects.master_audio_ref is empty; run NarrationMasterAssembler (C-016) first"
        )
    narration_path = (project_root / narration_master.file_path).resolve()
    if not narration_path.is_file():
        raise MasterAudioNotReadyError(f"narration_master file missing on disk: {narration_path}")


def _resolve_bgm_source(project_root: Path, bgm_candidate: BgmCandidate) -> Path:
    """Return the absolute path to the raw BGM source for the candidate."""
    return (project_root / bgm_candidate.raw_bgm_url).resolve()


def _ffmpeg_bin() -> str:
    found = shutil.which("ffmpeg")
    if not found:
        raise RuntimeError("ffmpeg binary not found on PATH")
    return found


def _build_filter_complex(envelope: EnvelopeSpec, narration_duration_s: float) -> str:
    """Build the two-input mix graph: narration as [0], BGM as [1]."""
    fade_in_s = envelope.fade_in_ms / 1000.0
    fade_out_s = envelope.fade_out_ms / 1000.0
    fade_out_start = max(narration_duration_s - fade_out_s, 0.0)
    return (
        f"[1:a]volume={envelope.bgm_gain_db}dB,"
        f"afade=t=in:st=0:d={fade_in_s},"
        f"afade=t=out:st={fade_out_start}:d={fade_out_s}[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=0[out]"
    )


def _run_mix(
    narration_path: Path,
    bgm_path: Path,
    out_path: Path,
    envelope: EnvelopeSpec,
    narration_duration_s: float,
) -> None:
    """Invoke ffmpeg to produce the deterministic mix file at out_path."""
    ffmpeg = _ffmpeg_bin()
    filter_complex = _build_filter_complex(envelope, narration_duration_s)
    cmd = [
        ffmpeg,
        "-y",
        "-v",
        "error",
        "-i",
        str(narration_path),
        "-i",
        str(bgm_path),
        "-filter_complex",
        filter_complex,
        "-map",
        "[out]",
        "-ac",
        "1",
        "-ar",
        "44100",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        # Strip muxer-side metadata so two invocations on identical
        # inputs produce byte-identical output (AC-1).
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
        raise RuntimeError(f"ffmpeg mix failed (rc={proc.returncode}): {proc.stderr.strip()}")


__all__ = [
    "AudioMixPreviewService",
    "MasterAudioNotReadyError",
    "PHASE_DIR",
]
