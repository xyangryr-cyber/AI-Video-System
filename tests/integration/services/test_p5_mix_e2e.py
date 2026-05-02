"""Integration tests for [SPEC-C-017] P5 mix pipeline (preview + master + exception).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-2.

Covers the Completion Definition's e2e expectation:
  * deterministic mix (preview + master both stable for fixed inputs)
  * master switchover (project_state.master_audio_ref swaps narration -> bgm_mix)
  * exception path (MasterAudioNotReadyError before narration is staged)

AC-4 (ffprobe sample-rate/channel equality with narration) is also exercised
here because it is the only AC that compares the preview + master files
against the narration end-to-end.
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (FFMPEG and FFPROBE),
    reason="ffmpeg / ffprobe required for SPEC-C-017 integration",
)


def _make_mp3(path: Path, duration_s: float, freq_hz: int) -> None:
    assert FFMPEG is not None
    subprocess.run(
        [
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
        ],
        check=True,
    )


def _seed_db(conn: sqlite3.Connection, project_id: str) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.execute("ALTER TABLE projects ADD COLUMN master_audio_ref TEXT")
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    conn.commit()


def _ffprobe(path: Path) -> Dict[str, Any]:
    assert FFPROBE is not None
    out = subprocess.run(
        [
            FFPROBE,
            "-v",
            "error",
            "-select_streams",
            "a:0",
            "-show_entries",
            "stream=sample_rate,channels:format=duration",
            "-of",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    data = json.loads(out.stdout)
    stream = data["streams"][0]
    return {
        "sample_rate": int(stream["sample_rate"]),
        "channels": int(stream["channels"]),
        "duration": float(data["format"]["duration"]),
    }


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
        rationale="e2e",
        raw_bgm_url=raw_bgm_rel,
    )


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


@pytest.fixture
def p5_project(
    tmp_path: Path,
) -> Iterator[Tuple[str, Path, sqlite3.Connection, Any, Any, Any]]:
    from src.backend.services.audio_envelope import EnvelopeSpec

    project_id = "proj_c017_e2e"
    project_root = tmp_path / project_id

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _seed_db(conn, project_id)
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


# ---------- e2e deterministic mix (preview + master) ------------------


class TestDeterministicMixE2E:
    """Running the full preview + master flow twice must produce identical bytes."""

    def test_preview_and_master_bytes_stable_across_reruns(
        self,
        p5_project: Tuple[str, Path, sqlite3.Connection, Any, Any, Any],
        tmp_path: Path,
    ) -> None:
        from src.backend.services.audio_mix_preview_service import (
            AudioMixPreviewService,
        )
        from src.backend.services.bgm_mix_renderer import BgmMixRenderer

        project_id, project_root, conn, narration, bgm, envelope = p5_project

        preview_path = AudioMixPreviewService(conn).render_preview(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )
        first_preview_bytes = preview_path.read_bytes()

        artifact_1 = BgmMixRenderer(conn).render_master(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )
        master_path = project_root / "phase_5" / "bgm_mix_master.mp3"
        first_master_bytes = master_path.read_bytes()

        # Rerun both stages; bytes + artifact checksum must match.
        preview_path.unlink(missing_ok=True)
        preview_path_2 = AudioMixPreviewService(conn).render_preview(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )
        assert preview_path_2.read_bytes() == first_preview_bytes

        artifact_2 = BgmMixRenderer(conn).render_master(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )
        assert master_path.read_bytes() == first_master_bytes
        assert artifact_1.checksum == artifact_2.checksum


# ---------- e2e master switchover -------------------------------------


class TestMasterSwitchoverE2E:
    """master_audio_ref kind flips narration_master -> bgm_mix_master after render_master."""

    def test_ref_kind_switches_to_bgm_mix_master(
        self,
        p5_project: Tuple[str, Path, sqlite3.Connection, Any, Any, Any],
    ) -> None:
        from src.backend.services.audio_mix_preview_service import (
            AudioMixPreviewService,
        )
        from src.backend.services.bgm_mix_renderer import BgmMixRenderer

        project_id, project_root, conn, narration, bgm, envelope = p5_project

        # Preview first (should stay on narration_master).
        AudioMixPreviewService(conn).render_preview(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )
        mid = json.loads(
            conn.execute(
                "SELECT master_audio_ref FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()["master_audio_ref"]
        )
        assert mid["kind"] == "narration_master"

        # Then master (should swap to bgm_mix_master).
        BgmMixRenderer(conn).render_master(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )
        final = json.loads(
            conn.execute(
                "SELECT master_audio_ref FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()["master_audio_ref"]
        )
        assert final["kind"] == "bgm_mix_master"
        assert final["based_on_phase"] == 5

        # AC-4 inline: ffprobe preview + master against narration metadata.
        narration_meta = _ffprobe(project_root / narration.file_path)
        preview_path = (
            project_root / "phase_5" / f"bgm_mix_preview_{bgm.candidate_id}.mp3"
        )
        preview_meta = _ffprobe(preview_path)
        master_meta = _ffprobe(project_root / "phase_5" / "bgm_mix_master.mp3")
        assert preview_meta["sample_rate"] == narration_meta["sample_rate"]
        assert preview_meta["channels"] == narration_meta["channels"]
        assert master_meta["sample_rate"] == narration_meta["sample_rate"]
        assert master_meta["channels"] == narration_meta["channels"]


# ---------- e2e exception path ----------------------------------------


class TestExceptionPathE2E:
    """render_preview before narration staged -> MasterAudioNotReadyError."""

    def test_raises_before_narration_staged(self, tmp_path: Path) -> None:
        from src.backend.services.audio_envelope import EnvelopeSpec
        from src.backend.services.audio_mix_preview_service import (
            AudioMixPreviewService,
            MasterAudioNotReadyError,
        )
        from src.shared.schemas.audio_master import NarrationMasterArtifact

        project_id = "proj_c017_missing_e2e"
        project_root = tmp_path / project_id
        project_root.mkdir()
        (project_root / "phase_5" / "bgm_candidates").mkdir(parents=True)
        raw_rel = "phase_5/bgm_candidates/bgm_e2e.mp3"
        _make_mp3(project_root / raw_rel, 1.0, 220)

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        _seed_db(conn, project_id)
        # no master_audio_ref seeded

        narration = NarrationMasterArtifact(
            kind="narration_master",
            file_path="phase_4/narration_master.mp3",
            based_on_phase=4,
            derived_from_segments=["seg_01"],
            total_duration_seconds=1.0,
            checksum="sha256:" + "0" * 64,
            version=1,
        )
        bgm = _candidate(
            "cand_bgm_e2e",
            raw_rel,
            "phase_5/bgm_mix_preview_cand_bgm_e2e.mp3",
        )
        envelope = EnvelopeSpec(bgm_gain_db=-10.0, fade_in_ms=100, fade_out_ms=100)

        try:
            with pytest.raises(MasterAudioNotReadyError):
                AudioMixPreviewService(conn).render_preview(
                    project_id,
                    project_root,
                    narration,
                    bgm,
                    envelope,
                )
        finally:
            conn.close()
