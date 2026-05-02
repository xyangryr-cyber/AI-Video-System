"""[SPEC-C-017] BgmMixRenderer -- P5 master (narration + chosen BGM) mix.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-2.

Invoked once the user confirms a BGM candidate. Emits
``phase_5/bgm_mix_master.mp3`` + side-car ``bgm_mix_master.json`` (SPEC-A-013
``BgmMixMasterArtifact``), pins ``source_ref.checksum`` to the upstream
narration master checksum (AC-2), and atomically flips
``projects.master_audio_ref`` from narration_master -> bgm_mix_master (AC-3).

Transactional contract: any failure after we start touching disk/DB rolls
back both the SQLite UPDATE (we drive commit/rollback ourselves) AND any
partially-written master files -- matching C-016 NarrationMasterAssembler.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

from src.backend.repositories.project_state_repo import (
    ProjectStateRepository,
)
from src.backend.services.audio_envelope import EnvelopeSpec
from src.backend.services.audio_mix_preview_service import (
    _assert_narration_ready,
    _resolve_bgm_source,
    _run_mix,
)
from src.shared.schemas.audio_master import (
    BgmMixMasterArtifact,
    NarrationMasterArtifact,
    SourceRef,
    validate_checksum_chain,
)
from src.shared.schemas.bgm_candidate import BgmCandidate

PHASE_DIR = "phase_5"
_MASTER_STEM = "bgm_mix_master"


class BgmMixRenderer:
    """Render the confirmed narration+BGM master and swap master_audio_ref."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn
        self._repo = ProjectStateRepository(conn)

    def render_master(
        self,
        project_id: str,
        project_root: Path,
        narration_master: NarrationMasterArtifact,
        selected_bgm: BgmCandidate,
        envelope: EnvelopeSpec,
    ) -> BgmMixMasterArtifact:
        _assert_narration_ready(self._repo, project_id, project_root, narration_master)

        narration_path = (project_root / narration_master.file_path).resolve()
        bgm_path = _resolve_bgm_source(project_root, selected_bgm)

        phase_dir = project_root / PHASE_DIR
        phase_dir.mkdir(parents=True, exist_ok=True)

        final_mp3 = phase_dir / f"{_MASTER_STEM}.mp3"
        final_json = phase_dir / f"{_MASTER_STEM}.json"
        tmp_mp3 = phase_dir / f"_{_MASTER_STEM}.tmp.mp3"
        tmp_json = phase_dir / f"_{_MASTER_STEM}.tmp.json"

        for tmp in (tmp_mp3, tmp_json):
            tmp.unlink(missing_ok=True)

        next_version = self._next_version(project_id)

        try:
            _run_mix(
                narration_path=narration_path,
                bgm_path=bgm_path,
                out_path=tmp_mp3,
                envelope=envelope,
                narration_duration_s=narration_master.total_duration_seconds,
            )
            checksum = _sha256_of_file(tmp_mp3)

            artifact = BgmMixMasterArtifact(
                kind="bgm_mix_master",
                file_path=f"{PHASE_DIR}/{_MASTER_STEM}.mp3",
                based_on_phase=5,
                derived_from_segments=list(narration_master.derived_from_segments),
                total_duration_seconds=narration_master.total_duration_seconds,
                checksum=checksum,
                version=next_version,
                source_ref=SourceRef(
                    kind="narration_master",
                    checksum=narration_master.checksum,
                ),
            )
            # Fail fast if the source_ref checksum drifted (defensive; AC-2).
            validate_checksum_chain(artifact, narration_master)

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


def _compact_ref(artifact: BgmMixMasterArtifact) -> dict[str, Any]:
    return {
        "kind": artifact.kind,
        "file_path": artifact.file_path,
        "based_on_phase": artifact.based_on_phase,
        "checksum": artifact.checksum,
        "version": artifact.version,
    }


__all__ = ["BgmMixRenderer"]
