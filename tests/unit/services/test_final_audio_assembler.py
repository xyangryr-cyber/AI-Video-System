"""Tests for [SPEC-C-019] FinalAudioAssembler (P6 final master audio).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-4.

Covers:
  AC-2: total_duration = sum of sfx_applied_segments (±50ms);
        source_ref.checksum chains back to base_master.checksum.
  AC-3: user_confirmed_layout=False -> LayoutNotConfirmedError and no artifact
        (mp3 / json / master_audio_ref left untouched).
  AC-6: master_audio_ref becomes {kind=final_audio_master, based_on_phase=6}.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Iterator, List, Tuple

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (FFMPEG and FFPROBE),
    reason="ffmpeg / ffprobe required for SPEC-C-019 audio tests",
)


def _make_sine_mp3(path: Path, duration_s: float, freq_hz: int) -> None:
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


def _ffprobe_duration(path: Path) -> float:
    assert FFPROBE is not None
    out = subprocess.run(
        [
            FFPROBE,
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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


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
    project_id: str,
    project_root: Path,
    conn: sqlite3.Connection,
    seg_durations: List[float],
) -> Any:
    from src.backend.services.narration_master_assembler import (
        NarrationMasterAssembler,
    )

    phase_4 = project_root / "phase_4"
    phase_4.mkdir(parents=True, exist_ok=True)
    entries = []
    for i, dur in enumerate(seg_durations, start=1):
        stem = f"seg_{i:02d}"
        _make_sine_mp3(phase_4 / f"{stem}.mp3", dur, 440)
        entries.append({"segment_id": stem, "audio_path": f"phase_4/{stem}.mp3"})
    (phase_4 / "timeline.json").write_text(
        json.dumps({"segments": entries}), encoding="utf-8"
    )
    return NarrationMasterAssembler(conn).assemble(project_id, project_root)


def _trigger(
    trigger_id: str,
    planned_time_sec: float,
    duration_seconds: float,
) -> Any:
    from src.shared.schemas.sfx_layout_plan import (
        SfxLayoutTrigger,
        SfxScriptAnchor,
    )

    return SfxLayoutTrigger(
        trigger_id=trigger_id,
        script_anchor=SfxScriptAnchor(span_id="span_01", text="x"),
        keyword_span=[0, 1],
        planned_time_sec=planned_time_sec,
        sfx_type="whoosh",
        rationale="t",
        narrative_role="emphasis",
        volume_db=0.0,
        duration_seconds=duration_seconds,
    )


def _sfx_resolver(sfx_dir: Path) -> Any:
    def _resolve(trigger: Any) -> Path:
        return sfx_dir / f"{trigger.sfx_type}.mp3"

    return _resolve


@pytest.fixture
def prepared_segments(
    tmp_path: Path,
) -> Iterator[Tuple[str, Path, sqlite3.Connection, Any, Any]]:
    """Mix three segments up-front and yield the mix artifact + base_master."""
    from src.backend.services.sfx_segment_mix_service import (
        SfxSegmentMixService,
    )
    from src.shared.schemas.sfx_mix_segments import SfxMixSegments

    project_id = "proj_c019_final"
    project_root = tmp_path / project_id
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _seed_schema(conn)
    _seed_project(conn, project_id)

    narration = _stage_narration(project_id, project_root, conn, [1.0, 1.0, 1.0])

    sfx_dir = project_root / "assets" / "sfx_library"
    sfx_dir.mkdir(parents=True)
    _make_sine_mp3(sfx_dir / "whoosh.mp3", 0.3, 2000)
    resolver = _sfx_resolver(sfx_dir)

    svc = SfxSegmentMixService(conn)
    svc.mix_segment(
        project_id,
        project_root,
        "seg_01",
        narration,
        [_trigger("trg_001", planned_time_sec=0.3, duration_seconds=0.2)],
        resolver,
    )
    svc.mix_segment(
        project_id,
        project_root,
        "seg_02",
        narration,
        [_trigger("trg_002", planned_time_sec=1.3, duration_seconds=0.2)],
        resolver,
    )
    svc.mix_segment(
        project_id,
        project_root,
        "seg_03",
        narration,
        [],
        resolver,
    )

    payload = json.loads(
        (project_root / "phase_6" / "sfx_mix_segments.json").read_text(encoding="utf-8")
    )
    mix = SfxMixSegments.model_validate(payload)

    try:
        yield project_id, project_root, conn, narration, mix
    finally:
        conn.close()


# ---------- AC-2 -------------------------------------------------------


class TestAC2AssembleTotalDurationAndChain:
    """AC-2: duration sums ±50ms and source_ref.checksum chains to base."""

    def test_assemble_total_duration(
        self,
        prepared_segments: Tuple[str, Path, sqlite3.Connection, Any, Any],
    ) -> None:
        from src.backend.services.final_audio_assembler import (
            FinalAudioAssembler,
        )

        project_id, project_root, conn, narration, mix = prepared_segments
        artifact = FinalAudioAssembler(conn).assemble(
            project_id=project_id,
            project_root=project_root,
            sfx_mix_segments=mix,
            base_master=narration,
            user_confirmed_layout=True,
        )
        final_path = project_root / artifact.file_path
        probed = _ffprobe_duration(final_path)

        expected = 0.0
        for seg in mix.segments:
            expected += _ffprobe_duration(project_root / seg.file_path)

        assert abs(probed - expected) <= 0.05, (
            f"final duration {probed:.4f} vs sum {expected:.4f} >50ms tolerance"
        )
        assert abs(artifact.total_duration_seconds - expected) <= 0.05

    def test_checksum_chain_to_base(
        self,
        prepared_segments: Tuple[str, Path, sqlite3.Connection, Any, Any],
    ) -> None:
        from src.backend.services.final_audio_assembler import (
            FinalAudioAssembler,
        )

        project_id, project_root, conn, narration, mix = prepared_segments
        artifact = FinalAudioAssembler(conn).assemble(
            project_id=project_id,
            project_root=project_root,
            sfx_mix_segments=mix,
            base_master=narration,
            user_confirmed_layout=True,
        )
        assert artifact.kind == "final_audio_master"
        assert artifact.source_ref.kind == narration.kind
        assert artifact.source_ref.checksum == narration.checksum
        assert artifact.checksum == _sha256(project_root / artifact.file_path)

        # Side-car json hydrates cleanly against A-013 discriminated union.
        side = project_root / "phase_6" / "final_audio_with_bgm_sfx.json"
        from src.shared.schemas.audio_master import (
            MasterAudioArtifactAdapter,
        )

        hydrated = MasterAudioArtifactAdapter.validate_python(
            json.loads(side.read_text(encoding="utf-8"))
        )
        assert hydrated.kind == "final_audio_master"


# ---------- AC-3 -------------------------------------------------------


class TestAC3LayoutNotConfirmed:
    """AC-3: unconfirmed layout raises and writes NO artifact."""

    def test_layout_not_confirmed_raises(
        self,
        prepared_segments: Tuple[str, Path, sqlite3.Connection, Any, Any],
    ) -> None:
        from src.backend.exceptions.sfx_exceptions import (
            LayoutNotConfirmedError,
        )
        from src.backend.services.final_audio_assembler import (
            FinalAudioAssembler,
        )

        project_id, project_root, conn, narration, mix = prepared_segments

        # Capture baseline: no final master on disk, no final ref in DB.
        final_mp3 = project_root / "phase_6" / "final_audio_with_bgm_sfx.mp3"
        final_json = project_root / "phase_6" / "final_audio_with_bgm_sfx.json"
        assert not final_mp3.exists()
        assert not final_json.exists()
        row_before = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        ref_before = json.loads(row_before["master_audio_ref"])
        assert ref_before["kind"] == "narration_master"

        with pytest.raises(LayoutNotConfirmedError):
            FinalAudioAssembler(conn).assemble(
                project_id=project_id,
                project_root=project_root,
                sfx_mix_segments=mix,
                base_master=narration,
                user_confirmed_layout=False,
            )

        assert not final_mp3.exists(), "final mp3 must not be written"
        assert not final_json.exists(), "final json must not be written"
        row_after = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        ref_after = json.loads(row_after["master_audio_ref"])
        assert ref_after["kind"] == "narration_master", (
            "master_audio_ref must not flip when layout unconfirmed"
        )


# ---------- AC-7 (mirrors SfxSegmentMixService) ------------------------


class TestAC7FinalAssemblerInvalidBaseMaster:
    """FinalAudioAssembler must reject a FinalAudioMasterArtifact as
    base_master with InvalidBaseMasterError (not LayoutNotConfirmedError)."""

    def test_final_assembler_invalid_base_master_raises(
        self,
        prepared_segments: Tuple[str, Path, sqlite3.Connection, Any, Any],
    ) -> None:
        from src.backend.exceptions.sfx_exceptions import (
            InvalidBaseMasterError,
        )
        from src.backend.services.final_audio_assembler import (
            FinalAudioAssembler,
        )
        from src.shared.schemas.audio_master import (
            FinalAudioMasterArtifact,
            SourceRef,
        )

        project_id, project_root, conn, narration, mix = prepared_segments
        bad_base = FinalAudioMasterArtifact(
            kind="final_audio_master",
            file_path="phase_6/final_audio_with_bgm_sfx.mp3",
            based_on_phase=6,
            derived_from_segments=list(narration.derived_from_segments),
            total_duration_seconds=narration.total_duration_seconds,
            checksum=narration.checksum,
            version=1,
            source_ref=SourceRef(kind="narration_master", checksum=narration.checksum),
        )
        with pytest.raises(InvalidBaseMasterError):
            FinalAudioAssembler(conn).assemble(
                project_id=project_id,
                project_root=project_root,
                sfx_mix_segments=mix,
                base_master=bad_base,
                user_confirmed_layout=True,
            )


# ---------- AC-6 -------------------------------------------------------


class TestAC6MasterAudioRefFinalKind:
    """AC-6: projects.master_audio_ref = {kind=final_audio_master, phase=6}."""

    def test_master_audio_ref_final_kind(
        self,
        prepared_segments: Tuple[str, Path, sqlite3.Connection, Any, Any],
    ) -> None:
        from src.backend.services.final_audio_assembler import (
            FinalAudioAssembler,
        )

        project_id, project_root, conn, narration, mix = prepared_segments
        artifact = FinalAudioAssembler(conn).assemble(
            project_id=project_id,
            project_root=project_root,
            sfx_mix_segments=mix,
            base_master=narration,
            user_confirmed_layout=True,
        )
        row = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        ref = json.loads(row["master_audio_ref"])
        assert ref["kind"] == "final_audio_master"
        assert ref["based_on_phase"] == 6
        assert ref["checksum"] == artifact.checksum
        assert ref["file_path"] == "phase_6/final_audio_with_bgm_sfx.mp3"
        assert ref["version"] >= 2
