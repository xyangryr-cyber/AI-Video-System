"""Tests for [SPEC-C-016] NarrationMasterAssembler (P4 主音频拼接).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-1.

Each test class maps to one AC from the task card (C-016):
  AC-1 lossless concat (frame-byte equality)
  AC-2 missing segment -> MissingSegmentError + no master + no DB update
  AC-3 checksum stable across reruns
  AC-4 projects.master_audio_ref persisted + passes A-013 schema
  AC-5 concat failure -> transactional rollback (no master file, no DB)
  AC-6 metadata fields + version increments on rerun
"""

from __future__ import annotations

import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Iterator, Tuple

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (FFMPEG and FFPROBE),
    reason="ffmpeg / ffprobe required for SPEC-C-016 audio tests",
)


# ---------- fixtures ------------------------------------------------


def _make_mp3(path: Path, duration_s: float, freq_hz: int) -> None:
    """Synthesize a fixed-codec MP3 tone at ``freq_hz``."""
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
    # Mirror V006 (SPEC-B-013) so tests exercise the real column.
    conn.execute("ALTER TABLE projects ADD COLUMN master_audio_ref TEXT")
    conn.commit()


def _seed_project(conn: sqlite3.Connection, project_id: str) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    conn.commit()


@pytest.fixture
def three_segment_project(
    tmp_path: Path,
) -> Iterator[Tuple[str, Path, sqlite3.Connection]]:
    project_id = "proj_c016"
    project_root = tmp_path / project_id
    phase_4 = project_root / "phase_4"
    phase_4.mkdir(parents=True)
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

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _seed_schema(conn)
    _seed_project(conn, project_id)

    try:
        yield project_id, project_root, conn
    finally:
        conn.close()


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


# ---------- AC-1 ----------------------------------------------------


class TestAC1LosslessConcat:
    """AC-1: 3 seg narration -> narration_master.mp3, lossless."""

    def test_lossless_concat_three_segments(
        self, three_segment_project: Tuple[str, Path, sqlite3.Connection]
    ) -> None:
        from src.backend.services.narration_master_assembler import (
            NarrationMasterAssembler,
        )

        project_id, project_root, conn = three_segment_project
        NarrationMasterAssembler(conn).assemble(project_id, project_root)

        master_mp3 = project_root / "phase_4" / "narration_master.mp3"
        assert master_mp3.exists(), "narration_master.mp3 must exist"

        # Lossless == frames preserved byte-identically; verify by
        # checking the master equals the raw byte concatenation of the
        # three source MP3s (no transcoding, no metadata rewrite).
        expected_bytes = b"".join(
            (project_root / "phase_4" / f"seg_{i:02d}.mp3").read_bytes()
            for i in (1, 2, 3)
        )
        actual_bytes = master_mp3.read_bytes()
        assert actual_bytes == expected_bytes, (
            "concat demuxer with -c copy must preserve frames byte-for-byte"
        )


# ---------- AC-2 ----------------------------------------------------


class TestAC2MissingSegment:
    """AC-2: missing segment -> MissingSegmentError + no side effects."""

    def test_missing_segment_raises_and_no_master(
        self, three_segment_project: Tuple[str, Path, sqlite3.Connection]
    ) -> None:
        from src.backend.services.narration_master_assembler import (
            MissingSegmentError,
            NarrationMasterAssembler,
        )

        project_id, project_root, conn = three_segment_project
        (project_root / "phase_4" / "seg_02.mp3").unlink()

        with pytest.raises(MissingSegmentError):
            NarrationMasterAssembler(conn).assemble(project_id, project_root)

        master_mp3 = project_root / "phase_4" / "narration_master.mp3"
        master_json = project_root / "phase_4" / "narration_master.json"
        assert not master_mp3.exists()
        assert not master_json.exists()

        row = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert row["master_audio_ref"] is None, (
            "failed assemble must not update projects.master_audio_ref"
        )


# ---------- AC-3 ----------------------------------------------------


class TestAC3ChecksumStable:
    """AC-3: same input produces same sha256 across runs."""

    def test_checksum_stable_across_runs(
        self, three_segment_project: Tuple[str, Path, sqlite3.Connection]
    ) -> None:
        from src.backend.services.narration_master_assembler import (
            NarrationMasterAssembler,
        )

        project_id, project_root, conn = three_segment_project
        a1 = NarrationMasterAssembler(conn).assemble(project_id, project_root)
        a2 = NarrationMasterAssembler(conn).assemble(project_id, project_root)
        assert a1.checksum == a2.checksum
        assert a1.checksum.startswith("sha256:")


# ---------- AC-4 ----------------------------------------------------


class TestAC4MasterAudioRefPersisted:
    """AC-4: projects.master_audio_ref persisted + passes A-013 schema."""

    def test_master_audio_ref_persisted(
        self, three_segment_project: Tuple[str, Path, sqlite3.Connection]
    ) -> None:
        from src.backend.services.narration_master_assembler import (
            NarrationMasterAssembler,
        )
        from src.shared.schemas.audio_master import (
            MasterAudioArtifactAdapter,
        )
        from src.shared.schemas.project_state import MasterAudioRef

        project_id, project_root, conn = three_segment_project
        NarrationMasterAssembler(conn).assemble(project_id, project_root)

        row = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert row["master_audio_ref"] is not None

        payload = json.loads(row["master_audio_ref"])
        # Compact pointer exposed via ProjectState.
        MasterAudioRef.model_validate(payload)

        # Full artifact JSON on disk satisfies A-013.
        artifact_json = project_root / "phase_4" / "narration_master.json"
        full = json.loads(artifact_json.read_text(encoding="utf-8"))
        MasterAudioArtifactAdapter.validate_python(full)


# ---------- AC-5 ----------------------------------------------------


class TestAC5TransactionalRollback:
    """AC-5: concat failure => no master file, no DB update."""

    def test_failed_assemble_does_not_pollute_state(
        self,
        three_segment_project: Tuple[str, Path, sqlite3.Connection],
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from src.backend.services import audio_concat
        from src.backend.services.narration_master_assembler import (
            NarrationMasterAssembler,
        )

        project_id, project_root, conn = three_segment_project

        # Force concat to blow up mid-flight so we exercise the rollback
        # path deterministically (ffmpeg's tolerance of malformed inputs
        # varies by position in the concat list, so relying on a
        # corrupted segment is flaky).
        def _boom(*_args: object, **_kwargs: object) -> None:
            raise audio_concat.AudioConcatError("synthetic concat failure")

        monkeypatch.setattr(
            "src.backend.services.narration_master_assembler.concat_losslessly",
            _boom,
        )

        with pytest.raises(audio_concat.AudioConcatError):
            NarrationMasterAssembler(conn).assemble(project_id, project_root)

        master_mp3 = project_root / "phase_4" / "narration_master.mp3"
        master_json = project_root / "phase_4" / "narration_master.json"
        assert not master_mp3.exists(), "master mp3 must not remain"
        assert not master_json.exists(), "master json must not remain"

        row = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert row["master_audio_ref"] is None


# ---------- AC-6 ----------------------------------------------------


class TestAC6Metadata:
    """AC-6: metadata fields + version increments on rerun."""

    def test_metadata_fields(
        self, three_segment_project: Tuple[str, Path, sqlite3.Connection]
    ) -> None:
        from src.backend.services.narration_master_assembler import (
            NarrationMasterAssembler,
        )

        project_id, project_root, conn = three_segment_project
        artifact = NarrationMasterAssembler(conn).assemble(project_id, project_root)
        assert artifact.kind == "narration_master"
        assert artifact.based_on_phase == 4
        assert artifact.derived_from_segments == [
            "seg_01",
            "seg_02",
            "seg_03",
        ]
        assert artifact.version == 1
        assert artifact.file_path == "phase_4/narration_master.mp3"
        assert artifact.checksum.startswith("sha256:")

        master_mp3 = project_root / "phase_4" / "narration_master.mp3"
        probed = _ffprobe_duration(master_mp3)
        assert abs(artifact.total_duration_seconds - probed) < 0.1, (
            f"total_duration_seconds={artifact.total_duration_seconds} "
            f"vs ffprobe={probed}"
        )

    def test_version_increments_on_rerun(
        self, three_segment_project: Tuple[str, Path, sqlite3.Connection]
    ) -> None:
        from src.backend.services.narration_master_assembler import (
            NarrationMasterAssembler,
        )

        project_id, project_root, conn = three_segment_project
        a1 = NarrationMasterAssembler(conn).assemble(project_id, project_root)
        a2 = NarrationMasterAssembler(conn).assemble(project_id, project_root)
        a3 = NarrationMasterAssembler(conn).assemble(project_id, project_root)
        assert a1.version == 1
        assert a2.version == 2
        assert a3.version == 3
