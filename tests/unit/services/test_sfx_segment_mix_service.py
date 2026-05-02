"""Tests for [SPEC-C-019] SfxSegmentMixService (P6 per-segment SFX mix).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-4.

Covers:
  AC-1: `mix_segment()` lays SFX energy into the trigger window.
  AC-4: sfx_mix_segments.json stays consistent with per-segment mp3 files
        (each segment.file_path exists, declared checksum == on-disk sha256).
  AC-5: re-mixing a single segment leaves sibling segments untouched.
  AC-7: base_master kind must be narration_master or bgm_mix_master.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, Iterator, List, Tuple

import numpy as np
import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (FFMPEG and FFPROBE),
    reason="ffmpeg / ffprobe required for SPEC-C-019 audio tests",
)


def _make_sine_mp3(
    path: Path, duration_s: float, freq_hz: int, volume: float = 1.0
) -> None:
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
        "-af",
        f"volume={volume}",
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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _decode_pcm(path: Path, sr: int = 44100) -> Tuple[np.ndarray, int]:
    assert FFMPEG is not None
    proc = subprocess.run(
        [
            FFMPEG,
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(sr),
            "-f",
            "f32le",
            "pipe:1",
        ],
        check=True,
        capture_output=True,
    )
    arr = np.frombuffer(proc.stdout, dtype=np.float32).astype(np.float64)
    return arr, sr


def _rms(segment: np.ndarray) -> float:
    if segment.size == 0:
        return 0.0
    return float(np.sqrt(np.mean(segment * segment)))


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
    seg_freqs: List[int],
) -> Any:
    """Build `phase_4/seg_*.mp3` + timeline.json and return NarrationMasterArtifact."""
    from src.backend.services.narration_master_assembler import (
        NarrationMasterAssembler,
    )

    phase_4 = project_root / "phase_4"
    phase_4.mkdir(parents=True, exist_ok=True)
    seg_entries = []
    for i, (dur, freq) in enumerate(zip(seg_durations, seg_freqs), start=1):
        stem = f"seg_{i:02d}"
        _make_sine_mp3(phase_4 / f"{stem}.mp3", dur, freq)
        seg_entries.append({"segment_id": stem, "audio_path": f"phase_4/{stem}.mp3"})
    (phase_4 / "timeline.json").write_text(
        json.dumps({"segments": seg_entries}), encoding="utf-8"
    )
    return NarrationMasterAssembler(conn).assemble(project_id, project_root)


def _trigger(
    trigger_id: str,
    planned_time_sec: float,
    duration_seconds: float,
    volume_db: float = 0.0,
    sfx_type: str = "whoosh",
) -> Any:
    from src.shared.schemas.sfx_layout_plan import (
        SfxLayoutTrigger,
        SfxScriptAnchor,
    )

    return SfxLayoutTrigger(
        trigger_id=trigger_id,
        script_anchor=SfxScriptAnchor(span_id="span_01", text="hook"),
        keyword_span=[0, 4],
        planned_time_sec=planned_time_sec,
        sfx_type=sfx_type,
        rationale="unit test",
        narrative_role="emphasis",
        volume_db=volume_db,
        duration_seconds=duration_seconds,
    )


@pytest.fixture
def staged(
    tmp_path: Path,
) -> Iterator[Tuple[str, Path, sqlite3.Connection, Any, Path]]:
    """Project with 3x 1.0s narration segments (base_master = narration_master)."""
    project_id = "proj_c019_unit"
    project_root = tmp_path / project_id

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _seed_schema(conn)
    _seed_project(conn, project_id)

    narration = _stage_narration(
        project_id,
        project_root,
        conn,
        seg_durations=[1.0, 1.0, 1.0],
        seg_freqs=[440, 440, 440],
    )

    # SFX library used by the resolver closure in tests.
    sfx_dir = project_root / "assets" / "sfx_library"
    sfx_dir.mkdir(parents=True)
    _make_sine_mp3(sfx_dir / "whoosh.mp3", 0.4, 2000, volume=1.0)

    try:
        yield project_id, project_root, conn, narration, sfx_dir
    finally:
        conn.close()


def _sfx_resolver_factory(sfx_dir: Path) -> Any:
    def _resolve(trigger: Any) -> Path:
        return sfx_dir / f"{trigger.sfx_type}.mp3"

    return _resolve


# ---------- AC-1 -------------------------------------------------------


class TestAC1TriggerEnergyInWindow:
    """AC-1: SFX energy appears in the trigger window of the mixed segment."""

    def test_trigger_energy_in_window(
        self,
        staged: Tuple[str, Path, sqlite3.Connection, Any, Path],
    ) -> None:
        from src.backend.services.sfx_segment_mix_service import (
            SfxSegmentMixService,
        )

        project_id, project_root, conn, narration, sfx_dir = staged
        # seg_02 covers [1.0, 2.0) in the base_master timeline. Place a
        # 0.3s trigger at absolute t=1.3s -> offset 0.3 within seg_02.
        trig = _trigger(
            "trg_001",
            planned_time_sec=1.3,
            duration_seconds=0.3,
            volume_db=0.0,
        )
        svc = SfxSegmentMixService(conn)
        segment = svc.mix_segment(
            project_id=project_id,
            project_root=project_root,
            segment_id="seg_02",
            base_master=narration,
            triggers=[trig],
            sfx_resolver=_sfx_resolver_factory(sfx_dir),
        )

        out_path = project_root / segment.file_path
        pcm, sr = _decode_pcm(out_path)
        # seg_02 duration is ~1.0s; trigger window 0.3..0.6 within the segment.
        before = pcm[int(0.0 * sr) : int(0.3 * sr)]
        window = pcm[int(0.3 * sr) : int(0.6 * sr)]
        assert _rms(window) > _rms(before) * 1.05, (
            f"trigger window RMS={_rms(window):.4f} not louder than "
            f"pre-trigger RMS={_rms(before):.4f}"
        )


# ---------- AC-4 -------------------------------------------------------


class TestAC4SfxMixSegmentsJsonConsistentWithFs:
    """AC-4: JSON side-car mirrors the on-disk mp3 files byte-for-byte."""

    def test_sfx_mix_segments_json_consistent_with_fs(
        self,
        staged: Tuple[str, Path, sqlite3.Connection, Any, Path],
    ) -> None:
        from src.backend.services.sfx_segment_mix_service import (
            SfxSegmentMixService,
        )
        from src.shared.schemas.sfx_mix_segments import SfxMixSegments

        project_id, project_root, conn, narration, sfx_dir = staged
        svc = SfxSegmentMixService(conn)
        resolver = _sfx_resolver_factory(sfx_dir)

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

        mix_json = project_root / "phase_6" / "sfx_mix_segments.json"
        payload = json.loads(mix_json.read_text(encoding="utf-8"))
        mix = SfxMixSegments.model_validate(payload)

        # base_master must be narration_master .mp3 (AC-7 downstream).
        assert mix.base_master == narration.file_path

        seg_ids = {s.segment_id for s in mix.segments}
        assert seg_ids == {"seg_01", "seg_02", "seg_03"}
        for seg in mix.segments:
            disk = project_root / seg.file_path
            assert disk.is_file(), f"segment file missing: {disk}"
            assert seg.checksum == _sha256(disk)


# ---------- AC-5 -------------------------------------------------------


class TestAC5SingleSegmentRemixIsolation:
    """AC-5: remixing seg_02 must not touch seg_01 / seg_03 bytes."""

    def test_single_segment_remix_isolation(
        self,
        staged: Tuple[str, Path, sqlite3.Connection, Any, Path],
    ) -> None:
        from src.backend.services.sfx_segment_mix_service import (
            SfxSegmentMixService,
        )

        project_id, project_root, conn, narration, sfx_dir = staged
        svc = SfxSegmentMixService(conn)
        resolver = _sfx_resolver_factory(sfx_dir)

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

        seg1_path = project_root / "phase_6" / "sfx_applied_segments" / "seg_01.mp3"
        seg3_path = project_root / "phase_6" / "sfx_applied_segments" / "seg_03.mp3"
        seg1_before = _sha256(seg1_path)
        seg3_before = _sha256(seg3_path)

        # Re-mix only seg_02 with the same trigger list (idempotent).
        svc.mix_segment(
            project_id,
            project_root,
            "seg_02",
            narration,
            [_trigger("trg_002", planned_time_sec=1.3, duration_seconds=0.2)],
            resolver,
        )

        assert _sha256(seg1_path) == seg1_before, "seg_01 perturbed by seg_02 remix"
        assert _sha256(seg3_path) == seg3_before, "seg_03 perturbed by seg_02 remix"


# ---------- AC-7 -------------------------------------------------------


class TestAC7InvalidBaseMaster:
    """AC-7: non-{narration,bgm_mix}_master kinds are rejected."""

    def test_invalid_base_master_kind_raises(
        self,
        staged: Tuple[str, Path, sqlite3.Connection, Any, Path],
    ) -> None:
        from src.backend.exceptions.sfx_exceptions import (
            InvalidBaseMasterError,
        )
        from src.backend.services.sfx_segment_mix_service import (
            SfxSegmentMixService,
        )
        from src.shared.schemas.audio_master import (
            FinalAudioMasterArtifact,
            SourceRef,
        )

        project_id, project_root, conn, narration, sfx_dir = staged
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
        svc = SfxSegmentMixService(conn)
        with pytest.raises(InvalidBaseMasterError):
            svc.mix_segment(
                project_id=project_id,
                project_root=project_root,
                segment_id="seg_02",
                base_master=bad_base,
                triggers=[],
                sfx_resolver=_sfx_resolver_factory(sfx_dir),
            )
