"""Integration test for [SPEC-C-019] P6 pipeline (mix segments + assemble).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-4.

Covers the Completion Definition's e2e expectations:
  * normal path: SfxLayoutPlanner → N x mix_segment → FinalAudioAssembler
    produces phase_6 artifacts and flips master_audio_ref to final_audio_master
  * LayoutNotConfirmedError intercepts final assembly and leaves fs + DB intact
  * no_bgm path: base_master = narration_master (not bgm_mix_master)
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sqlite3
import subprocess
from pathlib import Path
from typing import Any, List

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")

pytestmark = pytest.mark.skipif(
    not (FFMPEG and FFPROBE),
    reason="ffmpeg / ffprobe required for SPEC-C-019 integration",
)


def _sine(path: Path, duration_s: float, freq_hz: int) -> None:
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


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _seed(conn: sqlite3.Connection, project_id: str) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.execute("ALTER TABLE projects ADD COLUMN master_audio_ref TEXT")
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    conn.commit()


def _stage_narration(
    project_id: str,
    project_root: Path,
    conn: sqlite3.Connection,
    durations: List[float],
) -> Any:
    from src.backend.services.narration_master_assembler import (
        NarrationMasterAssembler,
    )

    phase_4 = project_root / "phase_4"
    phase_4.mkdir(parents=True, exist_ok=True)
    entries = []
    for i, dur in enumerate(durations, start=1):
        stem = f"seg_{i:02d}"
        _sine(phase_4 / f"{stem}.mp3", dur, 440)
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
        script_anchor=SfxScriptAnchor(span_id="s1", text="t"),
        keyword_span=[0, 1],
        planned_time_sec=planned_time_sec,
        sfx_type="whoosh",
        rationale="e2e",
        narrative_role="emphasis",
        volume_db=0.0,
        duration_seconds=duration_seconds,
    )


# ---------- normal path (no_bgm) --------------------------------------


class TestP6NoBgmPath:
    """base_master = narration_master (no_bgm fallback)."""

    def test_happy_path_produces_final_master(self, tmp_path: Path) -> None:
        from src.backend.services.final_audio_assembler import (
            FinalAudioAssembler,
        )
        from src.backend.services.sfx_layout_planner import (
            SfxLayoutPlanner,
        )
        from src.backend.services.sfx_segment_mix_service import (
            SfxSegmentMixService,
        )
        from src.shared.schemas.sfx_mix_segments import (
            SfxMixSegments,
            validate_applied_triggers_against_plan,
        )

        project_id = "proj_c019_e2e_nobgm"
        project_root = tmp_path / project_id
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        _seed(conn, project_id)

        narration = _stage_narration(project_id, project_root, conn, [1.0, 1.0, 1.0])

        sfx_dir = project_root / "assets" / "sfx_library"
        sfx_dir.mkdir(parents=True)
        _sine(sfx_dir / "whoosh.mp3", 0.3, 2000)

        # Step 1 (layout planner just validates the LLM-shaped payload).
        plan_payload = {
            "plan_version": 1,
            "triggers": [
                {
                    "trigger_id": "trg_001",
                    "script_anchor": {"span_id": "s1", "text": "hook"},
                    "keyword_span": [0, 4],
                    "planned_time_sec": 0.3,
                    "sfx_type": "whoosh",
                    "rationale": "emphasis",
                    "narrative_role": "hook",
                    "volume_db": 0.0,
                    "duration_seconds": 0.2,
                },
                {
                    "trigger_id": "trg_002",
                    "script_anchor": {"span_id": "s2", "text": "beat"},
                    "keyword_span": [5, 9],
                    "planned_time_sec": 1.3,
                    "sfx_type": "whoosh",
                    "rationale": "beat",
                    "narrative_role": "emphasis",
                    "volume_db": 0.0,
                    "duration_seconds": 0.2,
                },
            ],
        }
        plan = SfxLayoutPlanner().plan_from_payload(plan_payload)

        # Step 2: mix each segment.
        def resolver(t: Any) -> Path:
            return sfx_dir / f"{t.sfx_type}.mp3"

        svc = SfxSegmentMixService(conn)
        svc.mix_segment(
            project_id,
            project_root,
            "seg_01",
            narration,
            [plan.triggers[0]],
            resolver,
        )
        svc.mix_segment(
            project_id,
            project_root,
            "seg_02",
            narration,
            [plan.triggers[1]],
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

        mix = SfxMixSegments.model_validate(
            json.loads(
                (project_root / "phase_6" / "sfx_mix_segments.json").read_text(
                    encoding="utf-8"
                )
            )
        )
        validate_applied_triggers_against_plan(mix, plan)

        # Step 3: final assembly (user_confirmed_layout=True).
        final = FinalAudioAssembler(conn).assemble(
            project_id=project_id,
            project_root=project_root,
            sfx_mix_segments=mix,
            base_master=narration,
            user_confirmed_layout=True,
        )
        assert final.kind == "final_audio_master"
        assert final.source_ref.kind == "narration_master"
        assert final.source_ref.checksum == narration.checksum
        assert (project_root / final.file_path).is_file()
        assert _sha256(project_root / final.file_path) == final.checksum

        ref = json.loads(
            conn.execute(
                "SELECT master_audio_ref FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()["master_audio_ref"]
        )
        assert ref["kind"] == "final_audio_master"
        assert ref["based_on_phase"] == 6
        conn.close()

    def test_unconfirmed_layout_rolls_back(self, tmp_path: Path) -> None:
        from src.backend.exceptions.sfx_exceptions import (
            LayoutNotConfirmedError,
        )
        from src.backend.services.final_audio_assembler import (
            FinalAudioAssembler,
        )
        from src.backend.services.sfx_segment_mix_service import (
            SfxSegmentMixService,
        )
        from src.shared.schemas.sfx_mix_segments import SfxMixSegments

        project_id = "proj_c019_e2e_block"
        project_root = tmp_path / project_id
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        _seed(conn, project_id)

        narration = _stage_narration(project_id, project_root, conn, [0.8, 0.8])
        sfx_dir = project_root / "assets" / "sfx_library"
        sfx_dir.mkdir(parents=True)
        _sine(sfx_dir / "whoosh.mp3", 0.3, 2000)

        def resolver(t: Any) -> Path:
            return sfx_dir / f"{t.sfx_type}.mp3"

        svc = SfxSegmentMixService(conn)
        svc.mix_segment(
            project_id,
            project_root,
            "seg_01",
            narration,
            [_trigger("trg_001", planned_time_sec=0.2, duration_seconds=0.2)],
            resolver,
        )
        svc.mix_segment(
            project_id,
            project_root,
            "seg_02",
            narration,
            [],
            resolver,
        )
        mix = SfxMixSegments.model_validate(
            json.loads(
                (project_root / "phase_6" / "sfx_mix_segments.json").read_text(
                    encoding="utf-8"
                )
            )
        )
        with pytest.raises(LayoutNotConfirmedError):
            FinalAudioAssembler(conn).assemble(
                project_id=project_id,
                project_root=project_root,
                sfx_mix_segments=mix,
                base_master=narration,
                user_confirmed_layout=False,
            )
        assert not (project_root / "phase_6" / "final_audio_with_bgm_sfx.mp3").exists()
        ref = json.loads(
            conn.execute(
                "SELECT master_audio_ref FROM projects WHERE project_id = ?",
                (project_id,),
            ).fetchone()["master_audio_ref"]
        )
        # still pointing at narration_master (no flip).
        assert ref["kind"] == "narration_master"
        conn.close()
