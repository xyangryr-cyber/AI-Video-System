"""[SPEC-C-016] NarrationMasterAssembler -- P4 narration master audio.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-1.

Reads ``phase_4/timeline.json`` + ``phase_4/seg_XX.mp3`` segment files,
concatenates them losslessly into ``phase_4/narration_master.mp3`` +
writes a side-car ``narration_master.json`` that satisfies the SPEC-A-013
``NarrationMasterArtifact`` schema, and persists the compact pointer on
``projects.master_audio_ref`` (SPEC-B-013 column).

Transactional contract (AC-5): if any step fails after the master files
or the DB row have been touched, the DB UPDATE is rolled back AND any
partially-materialised master mp3 / json is removed, so rerunning starts
from a clean slate.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from src.backend.repositories.project_state_repo import (
    ProjectStateRepository,
)
from src.backend.services.audio_concat import (
    AudioConcatError,
    concat_losslessly,
)
from src.shared.schemas.audio_master import NarrationMasterArtifact


class MissingSegmentError(FileNotFoundError):
    """Raised when ``timeline.json`` references a segment file that does not exist."""


class TimelineError(ValueError):
    """Raised when ``timeline.json`` is missing or malformed."""


_PHASE_DIR = "phase_4"
_MASTER_STEM = "narration_master"


class NarrationMasterAssembler:
    """Assemble P4 narration master audio and persist the pointer."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._repo = ProjectStateRepository(conn)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def assemble(
        self,
        project_id: str,
        project_root: Path,
    ) -> NarrationMasterArtifact:
        """Assemble ``phase_4/narration_master.{mp3,json}`` for ``project_id``.

        Raises:
            MissingSegmentError: a referenced segment file is missing.
            TimelineError: timeline.json cannot be read/parsed.
            AudioConcatError: ffmpeg concat failed (corrupt segments etc.).
            KeyError: project_id not found in DB.
        """
        phase_dir = Path(project_root) / _PHASE_DIR
        timeline_path = phase_dir / "timeline.json"
        segment_ids, segment_paths = self._read_timeline(timeline_path, phase_dir)

        # AC-2: validate all segment files up front.
        missing = [p for p in segment_paths if not p.is_file()]
        if missing:
            raise MissingSegmentError(
                "missing narration segment file(s): " + ", ".join(str(p) for p in missing)
            )

        final_mp3 = phase_dir / f"{_MASTER_STEM}.mp3"
        final_json = phase_dir / f"{_MASTER_STEM}.json"
        # Preserve real suffixes so ffmpeg / tools infer the format.
        tmp_mp3 = phase_dir / f"_{_MASTER_STEM}.tmp.mp3"
        tmp_json = phase_dir / f"_{_MASTER_STEM}.tmp.json"

        # Defensive cleanup of stale tmp files from a prior crash.
        for tmp in (tmp_mp3, tmp_json):
            tmp.unlink(missing_ok=True)

        # Pre-flight: pick the next version BEFORE touching anything so
        # that a DB read failure aborts before any file is written.
        next_version = self._next_version(project_id)

        try:
            # Step 1: concat -> tmp_mp3 (no re-encode).
            concat_losslessly(segment_paths, tmp_mp3)

            # Step 2: measure duration + checksum.
            duration_s = _probe_duration_seconds(tmp_mp3)
            checksum = _sha256_of_file(tmp_mp3)

            # Step 3: build & validate artifact (A-013 schema).
            artifact = NarrationMasterArtifact(
                kind="narration_master",
                file_path=f"{_PHASE_DIR}/{_MASTER_STEM}.mp3",
                based_on_phase=4,
                derived_from_segments=list(segment_ids),
                total_duration_seconds=round(duration_s, 6),
                checksum=checksum,
                version=next_version,
            )

            # Step 4: emit tmp side-car json.
            tmp_json.write_text(
                json.dumps(
                    artifact.model_dump(mode="json"),
                    sort_keys=True,
                    indent=2,
                ),
                encoding="utf-8",
            )

            # Step 5: transactional publish (DB update + atomic rename).
            compact = _compact_ref(artifact)
            self._repo.set_master_audio_ref(project_id, compact)
            tmp_mp3.replace(final_mp3)
            tmp_json.replace(final_json)
            self._conn.commit()
            return artifact
        except Exception:
            # AC-5 rollback: leave no master file and no DB pollution.
            try:
                self._conn.rollback()
            except sqlite3.Error:
                pass
            for p in (tmp_mp3, tmp_json, final_mp3, final_json):
                try:
                    p.unlink(missing_ok=True)
                except OSError:
                    pass
            raise

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    def _next_version(self, project_id: str) -> int:
        prev = self._repo.get_master_audio_ref(project_id)
        if prev is None:
            return 1
        # Any prior pointer (narration / bgm / final) still counts as
        # "version N" for narration re-publication.
        try:
            return int(prev["version"]) + 1
        except (KeyError, TypeError, ValueError):
            return 1

    @staticmethod
    def _read_timeline(
        timeline_path: Path,
        phase_dir: Path,
    ) -> tuple[list[str], list[Path]]:
        if not timeline_path.is_file():
            raise TimelineError(f"timeline.json not found at {timeline_path}")
        try:
            data = json.loads(timeline_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise TimelineError(f"timeline.json is not valid JSON: {exc}") from exc
        segments = data.get("segments")
        if not isinstance(segments, list) or not segments:
            raise TimelineError("timeline.json must contain a non-empty 'segments' list")
        ids: list[str] = []
        paths: list[Path] = []
        for i, seg in enumerate(segments):
            if not isinstance(seg, dict):
                raise TimelineError(f"segment #{i} is not an object")
            seg_id = seg.get("segment_id")
            audio_path = seg.get("audio_path")
            if not isinstance(seg_id, str) or not seg_id:
                raise TimelineError(f"segment #{i} missing 'segment_id'")
            if not isinstance(audio_path, str) or not audio_path:
                raise TimelineError(f"segment #{i} missing 'audio_path'")
            ids.append(seg_id)
            # audio_path is project-root-relative (e.g.
            # "phase_4/seg_01.mp3"); fall back to phase_dir-local
            # resolution for flexibility.
            candidate = (phase_dir.parent / audio_path).resolve()
            if not candidate.exists():
                # Try phase_dir-local.
                alt = (phase_dir / Path(audio_path).name).resolve()
                candidate = alt
            paths.append(candidate)
        return ids, paths


# ---- module-level helpers ---------------------------------------------


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _probe_duration_seconds(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise AudioConcatError("ffprobe binary not found on PATH")
    out = subprocess.run(
        [
            ffprobe,
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
    txt = out.stdout.strip()
    try:
        return float(txt)
    except ValueError as exc:
        raise AudioConcatError(f"ffprobe returned non-numeric duration {txt!r}") from exc


def _compact_ref(artifact: NarrationMasterArtifact) -> dict[str, Any]:
    """Shape the compact ProjectState.master_audio_ref pointer."""
    return {
        "kind": artifact.kind,
        "file_path": artifact.file_path,
        "based_on_phase": artifact.based_on_phase,
        "checksum": artifact.checksum,
        "version": artifact.version,
    }


__all__ = [
    "MissingSegmentError",
    "NarrationMasterAssembler",
    "TimelineError",
]
