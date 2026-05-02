"""Tests for [SPEC-C-017] BgmMixRenderer (P5 master mix render).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-2.

Covers ACs:
  AC-2: bgm_mix_master.source_ref.checksum == narration_master.checksum
        (validate_checksum_chain passes on the hydrated artifact).
  AC-3 (master half): render_master() MUST update master_audio_ref.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Iterator, Tuple

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (FFMPEG and FFPROBE),
    reason="ffmpeg / ffprobe required for SPEC-C-017 audio tests",
)


def _make_mp3(path: Path, duration_s: float, freq_hz: int) -> None:
    assert FFMPEG is not None
    cmd = [
        FFMPEG,
        "-y",
        "-v",
        "error",
        "-f",
        "lavfi",
        "-i",
        f"sine=frequency={freq_hz}:duration={duration_s}:sample_rate=44100",
        "-ac",
        "1",
        "-ar",
        "44100",
        "-c:a",
        "libmp3lame",
        "-b:a",
        "128k",
        "-write_xing",
        "0",
        "-id3v2_version",
        "0",
        str(path),
    ]
    subprocess.run(cmd, check=True)


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.execute("ALTER TABLE projects ADD COLUMN master_audio_ref TEXT")
    conn.commit()


def _seed_project(conn: sqlite3.Connection, project_id: str) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    conn.commit()


def _stage_narration(
    project_id: str, project_root: Path, conn: sqlite3.Connection
) -> Any:
    from src.backend.services.narration_master_assembler import (
        NarrationMasterAssembler,
    )

    phase_4 = project_root / "phase_4"
    phase_4.mkdir(parents=True, exist_ok=True)
    _make_mp3(phase_4 / "seg_01.mp3", 0.5, 440)
    _make_mp3(phase_4 / "seg_02.mp3", 0.5, 880)
    _make_mp3(phase_4 / "seg_03.mp3", 0.5, 1320)
    (phase_4 / "timeline.json").write_text(
        json.dumps(
            {
                "segments": [
                    {"segment_id": "seg_01", "audio_path": "phase_4/seg_01.mp3"},
                    {"segment_id": "seg_02", "audio_path": "phase_4/seg_02.mp3"},
                    {"segment_id": "seg_03", "audio_path": "phase_4/seg_03.mp3"},
                ]
            }
        ),
        encoding="utf-8",
    )
    return NarrationMasterAssembler(conn).assemble(project_id, project_root)


def _candidate(candidate_id: str, raw_bgm_rel: str, preview_rel: str) -> Any:
    from src.shared.schemas.bgm_candidate import BgmCandidate

    return BgmCandidate(
        candidate_id=candidate_id,
        preview_url=preview_rel,
        preview_type="audio",
        style_tags=["calm"],
        description="fixture",
        is_recommended=True,
        adjustable_params={},
        rationale="unit test",
        raw_bgm_url=raw_bgm_rel,
    )


@pytest.fixture
def staged(
    tmp_path: Path,
) -> Iterator[Tuple[str, Path, sqlite3.Connection, Any, Any, Any]]:
    from src.backend.services.audio_envelope import EnvelopeSpec

    project_id = "proj_c017"
    project_root = tmp_path / project_id

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _seed_schema(conn)
    _seed_project(conn, project_id)

    narration = _stage_narration(project_id, project_root, conn)

    bgm_dir = project_root / "phase_5" / "bgm_candidates"
    bgm_dir.mkdir(parents=True)
    raw_rel = "phase_5/bgm_candidates/bgm_01.mp3"
    _make_mp3(project_root / raw_rel, 2.0, 220)

    cid = "cand_bgm_01"
    bgm = _candidate(cid, raw_rel, f"phase_5/bgm_mix_preview_{cid}.mp3")
    envelope = EnvelopeSpec(bgm_gain_db=-12.0, fade_in_ms=200, fade_out_ms=300)

    try:
        yield project_id, project_root, conn, narration, bgm, envelope
    finally:
        conn.close()


# ---------- AC-2 ------------------------------------------------------


class TestAC2ChecksumChain:
    """AC-2: bgm_mix_master.source_ref.checksum == narration_master.checksum."""

    def test_master_source_ref_checksum_matches_narration(
        self,
        staged: Tuple[str, Path, sqlite3.Connection, Any, Any, Any],
    ) -> None:
        from src.backend.services.bgm_mix_renderer import BgmMixRenderer
        from src.shared.schemas.audio_master import (
            MasterAudioArtifactAdapter,
            validate_checksum_chain,
        )

        project_id, project_root, conn, narration, bgm, envelope = staged
        artifact = BgmMixRenderer(conn).render_master(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )

        assert artifact.kind == "bgm_mix_master"
        assert artifact.source_ref.kind == "narration_master"
        assert artifact.source_ref.checksum == narration.checksum

        master_json_path = project_root / "phase_5" / "bgm_mix_master.json"
        on_disk = json.loads(master_json_path.read_text(encoding="utf-8"))
        hydrated = MasterAudioArtifactAdapter.validate_python(on_disk)
        validate_checksum_chain(hydrated, narration)


# ---------- AC-3 (master half) ----------------------------------------


class TestAC3MasterUpdatesRef:
    """AC-3: render_master MUST update master_audio_ref to bgm_mix_master."""

    def test_master_updates_ref(
        self,
        staged: Tuple[str, Path, sqlite3.Connection, Any, Any, Any],
    ) -> None:
        from src.backend.services.bgm_mix_renderer import BgmMixRenderer

        project_id, project_root, conn, narration, bgm, envelope = staged
        artifact = BgmMixRenderer(conn).render_master(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )

        row = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        ref = json.loads(row["master_audio_ref"])
        assert ref["kind"] == "bgm_mix_master"
        assert ref["checksum"] == artifact.checksum
        assert ref["file_path"] == "phase_5/bgm_mix_master.mp3"
        assert ref["based_on_phase"] == 5
        assert ref["version"] >= 2
