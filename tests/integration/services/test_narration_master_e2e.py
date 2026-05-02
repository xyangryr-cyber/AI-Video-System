"""E2E integration test for [SPEC-C-016] NarrationMasterAssembler.

Covers the success path plus one failure path (missing segment) against
a real filesystem layout and a real SQLite DB with the V006
``master_audio_ref`` column applied.
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
    reason="ffmpeg / ffprobe required for SPEC-C-016 e2e",
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


@pytest.fixture
def e2e_project(
    tmp_path: Path,
) -> Iterator[Tuple[str, Path, sqlite3.Connection]]:
    project_id = "proj_c016_e2e"
    project_root = tmp_path / project_id
    phase_4 = project_root / "phase_4"
    phase_4.mkdir(parents=True)
    for idx, freq in enumerate((440, 660, 880), start=1):
        _make_mp3(phase_4 / f"seg_{idx:02d}.mp3", 0.4, freq)
    timeline = {
        "segments": [
            {
                "segment_id": f"seg_{i:02d}",
                "audio_path": f"phase_4/seg_{i:02d}.mp3",
            }
            for i in (1, 2, 3)
        ]
    }
    (phase_4 / "timeline.json").write_text(json.dumps(timeline), encoding="utf-8")

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.execute("ALTER TABLE projects ADD COLUMN master_audio_ref TEXT")
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "e2e", "e2e"),
    )
    conn.commit()

    try:
        yield project_id, project_root, conn
    finally:
        conn.close()


class TestE2ESuccess:
    def test_happy_path_emits_master_and_updates_db(
        self, e2e_project: Tuple[str, Path, sqlite3.Connection]
    ) -> None:
        from src.backend.services.narration_master_assembler import (
            NarrationMasterAssembler,
        )

        project_id, project_root, conn = e2e_project
        artifact = NarrationMasterAssembler(conn).assemble(project_id, project_root)

        master_mp3 = project_root / "phase_4" / "narration_master.mp3"
        master_json = project_root / "phase_4" / "narration_master.json"
        assert master_mp3.exists() and master_mp3.stat().st_size > 0
        assert master_json.exists()

        on_disk = json.loads(master_json.read_text(encoding="utf-8"))
        assert on_disk["checksum"] == artifact.checksum
        assert on_disk["kind"] == "narration_master"

        row = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        payload = json.loads(row["master_audio_ref"])
        assert payload["checksum"] == artifact.checksum
        assert payload["version"] == artifact.version
        assert payload["based_on_phase"] == 4


class TestE2EFailureIsAtomic:
    def test_missing_segment_leaves_fs_and_db_clean(
        self, e2e_project: Tuple[str, Path, sqlite3.Connection]
    ) -> None:
        from src.backend.services.narration_master_assembler import (
            MissingSegmentError,
            NarrationMasterAssembler,
        )

        project_id, project_root, conn = e2e_project
        (project_root / "phase_4" / "seg_03.mp3").unlink()

        with pytest.raises(MissingSegmentError):
            NarrationMasterAssembler(conn).assemble(project_id, project_root)

        assert not (project_root / "phase_4" / "narration_master.mp3").exists()
        assert not (project_root / "phase_4" / "narration_master.json").exists()
        row = conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        assert row["master_audio_ref"] is None
