"""Tests for [SPEC-C-017] AudioMixPreviewService (P5 mix preview).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-2.

Covers ACs:
  AC-1: preview render is deterministic (same inputs -> same bytes / sha256).
  AC-3 (preview half): render_preview() does NOT update master_audio_ref.
  AC-5: candidate-card schema: preview_url + raw_bgm_url both present;
        legacy callers sending only ``bgm_url`` get deprecated compat.
  AC-6: render_preview() on a project without narration_master -> raises
        MasterAudioNotReadyError.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
import warnings
from pathlib import Path
from typing import Any, Dict, Iterator, Tuple

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (FFMPEG and FFPROBE),
    reason="ffmpeg / ffprobe required for SPEC-C-017 audio tests",
)


# ---------- fixture helpers -------------------------------------------


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


def _stage_narration_master(
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
    timeline = {
        "segments": [
            {"segment_id": "seg_01", "audio_path": "phase_4/seg_01.mp3"},
            {"segment_id": "seg_02", "audio_path": "phase_4/seg_02.mp3"},
            {"segment_id": "seg_03", "audio_path": "phase_4/seg_03.mp3"},
        ]
    }
    (phase_4 / "timeline.json").write_text(json.dumps(timeline), encoding="utf-8")
    return NarrationMasterAssembler(conn).assemble(project_id, project_root)


def _build_bgm_candidate(
    candidate_id: str,
    raw_bgm_rel: str,
    preview_rel: str,
) -> Any:
    from src.shared.schemas.bgm_candidate import BgmCandidate

    return BgmCandidate(
        candidate_id=candidate_id,
        preview_url=preview_rel,
        preview_type="audio",
        style_tags=["calm"],
        description="test bgm",
        is_recommended=True,
        adjustable_params={},
        rationale="unit test fixture",
        raw_bgm_url=raw_bgm_rel,
    )


@pytest.fixture
def p5_project(
    tmp_path: Path,
) -> Iterator[Tuple[str, Path, sqlite3.Connection, Any, Any, Any]]:
    """Fully-staged P5 project: narration_master + phase_5/bgm candidate."""
    from src.backend.services.audio_envelope import EnvelopeSpec

    project_id = "proj_c017"
    project_root = tmp_path / project_id

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _seed_schema(conn)
    _seed_project(conn, project_id)

    narration_master = _stage_narration_master(project_id, project_root, conn)

    phase_5 = project_root / "phase_5" / "bgm_candidates"
    phase_5.mkdir(parents=True)
    raw_bgm_rel = "phase_5/bgm_candidates/bgm_01.mp3"
    _make_mp3(project_root / raw_bgm_rel, 2.0, 220)

    candidate_id = "cand_bgm_01"
    preview_rel = f"phase_5/bgm_mix_preview_{candidate_id}.mp3"
    bgm_candidate = _build_bgm_candidate(candidate_id, raw_bgm_rel, preview_rel)
    envelope = EnvelopeSpec(bgm_gain_db=-12.0, fade_in_ms=200, fade_out_ms=300)

    try:
        yield project_id, project_root, conn, narration_master, bgm_candidate, envelope
    finally:
        conn.close()


# ---------- AC-1 ------------------------------------------------------


class TestAC1Deterministic:
    """AC-1: fixed narration + fixed BGM + fixed envelope -> identical bytes."""

    def test_preview_deterministic_pcm(
        self,
        p5_project: Tuple[str, Path, sqlite3.Connection, Any, Any, Any],
    ) -> None:
        from src.backend.services.audio_mix_preview_service import (
            AudioMixPreviewService,
        )

        project_id, project_root, conn, narration, bgm, envelope = p5_project
        svc = AudioMixPreviewService(conn)

        preview_1 = svc.render_preview(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )
        bytes_1 = preview_1.read_bytes()

        preview_1.unlink()
        preview_2 = svc.render_preview(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )
        bytes_2 = preview_2.read_bytes()

        assert preview_1 == preview_2
        assert (
            hashlib.sha256(bytes_1).hexdigest() == hashlib.sha256(bytes_2).hexdigest()
        ), "render_preview must be deterministic for fixed inputs"


# ---------- AC-3 (preview half) ---------------------------------------


class TestAC3PreviewDoesNotUpdateRef:
    """AC-3: render_preview() must not touch master_audio_ref."""

    def test_preview_does_not_update_ref(
        self,
        p5_project: Tuple[str, Path, sqlite3.Connection, Any, Any, Any],
    ) -> None:
        from src.backend.services.audio_mix_preview_service import (
            AudioMixPreviewService,
        )

        project_id, project_root, conn, narration, bgm, envelope = p5_project
        before = json.loads(
            conn.execute(
                "SELECT master_audio_ref FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()["master_audio_ref"]
        )
        AudioMixPreviewService(conn).render_preview(
            project_id,
            project_root,
            narration,
            bgm,
            envelope,
        )
        after = json.loads(
            conn.execute(
                "SELECT master_audio_ref FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()["master_audio_ref"]
        )
        assert before == after, "render_preview must not touch master_audio_ref"
        assert after["kind"] == "narration_master"


# ---------- AC-5 ------------------------------------------------------


class TestAC5CandidateSchema:
    """AC-5: dual-url candidate + legacy bgm_url compat."""

    def test_candidate_card_preview_and_raw_urls(self) -> None:
        from src.shared.schemas.bgm_candidate import BgmCandidate

        card = BgmCandidate(
            candidate_id="cand_bgm_99",
            preview_url="phase_5/bgm_mix_preview_cand_bgm_99.mp3",
            preview_type="audio",
            style_tags=["calm"],
            description="dual-url card",
            is_recommended=False,
            adjustable_params={},
            rationale="AC-5",
            raw_bgm_url="phase_5/bgm_candidates/bgm_99.mp3",
        )
        assert card.preview_url.startswith("phase_5/bgm_mix_preview_")
        assert card.raw_bgm_url == "phase_5/bgm_candidates/bgm_99.mp3"

    def test_legacy_bgm_url_compat(self) -> None:
        from src.shared.schemas.bgm_candidate import BgmCandidate

        legacy_payload: Dict[str, Any] = {
            "candidate_id": "cand_bgm_legacy",
            "bgm_url": "phase_5/bgm_candidates/legacy.mp3",
            "preview_type": "audio",
            "style_tags": ["calm"],
            "description": "legacy caller",
            "is_recommended": False,
            "adjustable_params": {},
            "rationale": "AC-5 legacy",
        }
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            card = BgmCandidate.model_validate(legacy_payload)
        assert card.preview_url == "phase_5/bgm_candidates/legacy.mp3", (
            "legacy bgm_url must be promoted to preview_url for back-compat"
        )
        assert card.raw_bgm_url == "phase_5/bgm_candidates/legacy.mp3", (
            "legacy bgm_url must also populate raw_bgm_url (BgmCandidate requires it)"
        )
        assert any(
            issubclass(w.category, DeprecationWarning) and "bgm_url" in str(w.message)
            for w in caught
        ), "legacy bgm_url input must emit a DeprecationWarning"


# ---------- AC-6 ------------------------------------------------------


class TestAC6MissingNarrationMaster:
    """AC-6: render_preview without staged narration_master -> raises."""

    def test_missing_narration_master_raises(self, tmp_path: Path) -> None:
        from src.backend.services.audio_envelope import EnvelopeSpec
        from src.backend.services.audio_mix_preview_service import (
            AudioMixPreviewService,
            MasterAudioNotReadyError,
        )
        from src.shared.schemas.audio_master import NarrationMasterArtifact

        project_id = "proj_c017_missing"
        project_root = tmp_path / project_id
        project_root.mkdir()
        (project_root / "phase_5" / "bgm_candidates").mkdir(parents=True)
        raw_bgm_rel = "phase_5/bgm_candidates/bgm_missing.mp3"
        _make_mp3(project_root / raw_bgm_rel, 1.0, 220)

        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        _seed_schema(conn)
        _seed_project(conn, project_id)
        # NOTE: master_audio_ref intentionally NOT seeded.

        narration = NarrationMasterArtifact(
            kind="narration_master",
            file_path="phase_4/narration_master.mp3",
            based_on_phase=4,
            derived_from_segments=["seg_01"],
            total_duration_seconds=1.0,
            checksum="sha256:" + "0" * 64,
            version=1,
        )
        bgm = _build_bgm_candidate(
            "cand_bgm_missing",
            raw_bgm_rel,
            "phase_5/bgm_mix_preview_cand_bgm_missing.mp3",
        )
        envelope = EnvelopeSpec(bgm_gain_db=-12.0, fade_in_ms=100, fade_out_ms=100)

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
