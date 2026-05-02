"""[SPEC-C-019] FinalAudioAssembler -- P6 final master audio.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-4 item 2.

Given a validated ``SfxMixSegments`` artifact (N per-segment mp3 files
produced by ``SfxSegmentMixService``) and the upstream ``base_master``,
concatenates all segments into ``phase_6/final_audio_with_bgm_sfx.mp3``,
writes a SPEC-A-013 ``FinalAudioMasterArtifact`` side-car, and atomically
flips ``projects.master_audio_ref`` to the new final master.

Hard gate (AC-3): ``user_confirmed_layout`` MUST be True. If not, we
raise ``LayoutNotConfirmedError`` BEFORE touching the filesystem or the
DB so recovery is trivial.

Transactional contract: any failure after we start writing disk / DB
rolls both back together -- same pattern as
``NarrationMasterAssembler`` (C-016) and ``BgmMixRenderer`` (C-017).
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, cast

from src.backend.exceptions.sfx_exceptions import (
    InvalidBaseMasterError,
    LayoutNotConfirmedError,
)
from src.backend.repositories.project_state_repo import (
    ProjectStateRepository,
)
from src.backend.services.audio_concat import concat_losslessly
from src.backend.services.sfx_segment_mix_service import PHASE_6_DIR
from src.shared.schemas.audio_master import (
    BgmMixMasterArtifact,
    FinalAudioMasterArtifact,
    MasterAudioArtifact,
    NarrationMasterArtifact,
    SourceRef,
)
from src.shared.schemas.sfx_mix_segments import SfxMixSegments


_FINAL_STEM = "final_audio_with_bgm_sfx"


class FinalAudioAssembler:
    """Concatenate P6 per-segment mp3s into the final master."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._repo = ProjectStateRepository(conn)

    def assemble(
        self,
        project_id: str,
        project_root: Path,
        sfx_mix_segments: SfxMixSegments,
        base_master: MasterAudioArtifact,
        user_confirmed_layout: bool,
    ) -> FinalAudioMasterArtifact:
        if not user_confirmed_layout:
            raise LayoutNotConfirmedError(
                "FinalAudioAssembler.assemble requires user_confirmed_layout=True; "
                "no final master written"
            )
        if not isinstance(base_master, (NarrationMasterArtifact, BgmMixMasterArtifact)):
            raise InvalidBaseMasterError(
                f"base_master.kind must be narration_master or "
                f"bgm_mix_master; got {base_master.kind!r}"
            )
        if sfx_mix_segments.base_master != base_master.file_path:
            raise ValueError(
                "sfx_mix_segments.base_master "
                f"({sfx_mix_segments.base_master!r}) does not match "
                f"base_master.file_path ({base_master.file_path!r})"
            )

        segment_paths = [
            (project_root / seg.file_path).resolve()
            for seg in sfx_mix_segments.segments
        ]
        missing = [p for p in segment_paths if not p.is_file()]
        if missing:
            raise FileNotFoundError(
                "missing sfx_applied_segment file(s): "
                + ", ".join(str(p) for p in missing)
            )

        phase_dir = project_root / PHASE_6_DIR
        phase_dir.mkdir(parents=True, exist_ok=True)
        final_mp3 = phase_dir / f"{_FINAL_STEM}.mp3"
        final_json = phase_dir / f"{_FINAL_STEM}.json"
        tmp_mp3 = phase_dir / f"_{_FINAL_STEM}.tmp.mp3"
        tmp_json = phase_dir / f"_{_FINAL_STEM}.tmp.json"
        for tmp in (tmp_mp3, tmp_json):
            tmp.unlink(missing_ok=True)

        next_version = self._next_version(project_id)

        try:
            concat_losslessly(segment_paths, tmp_mp3)
            duration_s = _probe_duration_seconds(tmp_mp3)
            checksum = _sha256_of_file(tmp_mp3)

            artifact = FinalAudioMasterArtifact(
                kind="final_audio_master",
                file_path=f"{PHASE_6_DIR}/{_FINAL_STEM}.mp3",
                based_on_phase=6,
                derived_from_segments=list(base_master.derived_from_segments),
                total_duration_seconds=round(duration_s, 6),
                checksum=checksum,
                version=next_version,
                source_ref=SourceRef(
                    kind=cast(Any, base_master.kind),
                    checksum=base_master.checksum,
                ),
            )

            tmp_json.write_text(
                json.dumps(
                    artifact.model_dump(mode="json"),
                    sort_keys=True,
                    indent=2,
                ),
                encoding="utf-8",
            )

            self._repo.set_master_audio_ref(project_id, _compact_ref(artifact))
            tmp_mp3.replace(final_mp3)
            tmp_json.replace(final_json)
            self._conn.commit()
            return artifact
        except Exception:
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

    def _next_version(self, project_id: str) -> int:
        prev = self._repo.get_master_audio_ref(project_id)
        if prev is None:
            return 1
        try:
            return int(prev["version"]) + 1
        except (KeyError, TypeError, ValueError):
            return 1


def _sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _probe_duration_seconds(path: Path) -> float:
    ffprobe = shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe binary not found on PATH")
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
    return float(out.stdout.strip())


def _compact_ref(artifact: FinalAudioMasterArtifact) -> dict[str, Any]:
    return {
        "kind": artifact.kind,
        "file_path": artifact.file_path,
        "based_on_phase": artifact.based_on_phase,
        "checksum": artifact.checksum,
        "version": artifact.version,
    }


__all__ = ["FinalAudioAssembler"]
