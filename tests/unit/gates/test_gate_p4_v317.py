"""[SPEC-D-018] Gate-P4 upgrade -- 5 new v3.17 L1 checks + aggregate.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §D-AUDP7A-1.

Covers:
  AC-1: 5 new L1 checks each pass/fail independently (unit-level).
  AC-2: missing-segment aggregate -> concat FAIL, Gate FAIL, others PASS.
  AC-3: v3.15 7-item GateKeeper regression still PASS (not broken).
  AC-5: report structure lists both v3.17 + v3.15 checks with verdict/reason.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any, Iterator

import pytest

from src.backend.gates.audio_master_checks import (
    check_checksum_consistent,
    check_master_file_exists,
    check_master_playable,
)
from src.backend.gates.gate_p4 import (
    GateP4Checker,
    GateP4Result,
    check_concat_integrity,
    check_master_audio_ref_switched,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"


# ---------- helpers ------------------------------------------------


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return f"sha256:{h.hexdigest()}"


def _write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _write_timeline(phase_dir: Path, segments: list[dict[str, str]]) -> None:
    (phase_dir / "timeline.json").write_text(
        json.dumps({"segments": segments}), encoding="utf-8"
    )


def _build_master_files(
    phase_dir: Path,
    *,
    master_bytes: bytes,
    master_duration: float,
    segment_ids: list[str],
    checksum: str | None = None,
    kind: str = "narration_master",
    version: int = 1,
) -> tuple[Path, Path]:
    mp3 = phase_dir / "narration_master.mp3"
    js = phase_dir / "narration_master.json"
    _write_bytes(mp3, master_bytes)
    sha = checksum or _sha256(mp3)
    artifact = {
        "kind": kind,
        "file_path": "phase_4/narration_master.mp3",
        "based_on_phase": 4,
        "derived_from_segments": segment_ids,
        "total_duration_seconds": master_duration,
        "checksum": sha,
        "version": version,
    }
    js.write_text(json.dumps(artifact, sort_keys=True), encoding="utf-8")
    return mp3, js


def _fake_probe(durations: dict[Path, float]):
    def probe(path: Path) -> float:
        return durations.get(Path(path), 0.0)

    return probe


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    conn.execute("ALTER TABLE projects ADD COLUMN master_audio_ref TEXT")
    conn.commit()


def _seed_project_and_phase(
    conn: sqlite3.Connection,
    project_id: str,
    *,
    master_ref: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    if master_ref is not None:
        conn.execute(
            "UPDATE projects SET master_audio_ref = ? WHERE project_id = ?",
            (json.dumps(master_ref, sort_keys=True), project_id),
        )
    conn.commit()


def _seed_v315_gatep4_happy_path(conn: sqlite3.Connection, project_id: str) -> None:
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name, status, "
        "artifact_version, artifact_status, artifact_path, "
        "preferences_confirmed_at) VALUES(?, ?, ?, ?, ?, ?, ?, ?)",
        (
            project_id,
            4,
            "audio_master",
            "active",
            1,
            "ok",
            "phase_4/narration_master.mp3",
            "2026-04-24T00:00:00.000Z",
        ),
    )
    conn.execute(
        "INSERT INTO task_ledger(project_id, phase, type, status, "
        "target_version, result_ref, created_at) "
        "VALUES(?, ?, 'review', 'succeeded', ?, ?, "
        "strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
        (project_id, 4, 1, json.dumps({"verdict": "PASS", "blocking_issues": []})),
    )
    conn.execute(
        "INSERT INTO agent_call_log(project_id, phase, agent_name, model, "
        "tokens, duration_ms, prompt, response, created_at) "
        "VALUES(?, ?, 'NarrationMasterAssembler', 'n/a', 1, 0, '', '', "
        "strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
        (project_id, 4),
    )
    conn.commit()


# ---------- fixture ----------------------------------------------


@pytest.fixture
def happy_path_project(
    tmp_path: Path,
) -> Iterator[tuple[str, Path, sqlite3.Connection, dict[Path, float]]]:
    project_id = "proj_d018"
    project_root = tmp_path / project_id
    phase_dir = project_root / "phase_4"
    phase_dir.mkdir(parents=True)

    seg1 = phase_dir / "seg_01.mp3"
    seg2 = phase_dir / "seg_02.mp3"
    seg3 = phase_dir / "seg_03.mp3"
    _write_bytes(seg1, b"SEG-1-data")
    _write_bytes(seg2, b"SEG-2-data")
    _write_bytes(seg3, b"SEG-3-data")
    _write_timeline(
        phase_dir,
        [
            {"segment_id": "seg_01", "audio_path": "phase_4/seg_01.mp3"},
            {"segment_id": "seg_02", "audio_path": "phase_4/seg_02.mp3"},
            {"segment_id": "seg_03", "audio_path": "phase_4/seg_03.mp3"},
        ],
    )

    master_bytes = b"SEG-1-data" + b"SEG-2-data" + b"SEG-3-data"
    master_duration = 1.5
    durations = {
        seg1: 0.5,
        seg2: 0.5,
        seg3: 0.5,
        phase_dir / "narration_master.mp3": master_duration,
    }

    mp3, _ = _build_master_files(
        phase_dir,
        master_bytes=master_bytes,
        master_duration=master_duration,
        segment_ids=["seg_01", "seg_02", "seg_03"],
    )

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    _seed_schema(conn)
    _seed_project_and_phase(
        conn,
        project_id,
        master_ref={
            "kind": "narration_master",
            "file_path": "phase_4/narration_master.mp3",
            "based_on_phase": 4,
            "checksum": _sha256(mp3),
            "version": 1,
        },
    )
    _seed_v315_gatep4_happy_path(conn, project_id)

    try:
        yield project_id, project_root, conn, durations
    finally:
        conn.close()


# ---------- AC-1 -------------------------------------------------


class TestAC1:
    """5 new L1 checks each pass/fail independently."""

    def test_master_exists(self, tmp_path: Path) -> None:
        missing = tmp_path / "phase_4" / "narration_master.mp3"
        result = check_master_file_exists(missing)
        assert result.passed is False
        assert (
            "not found" in result.reason.lower() or "missing" in result.reason.lower()
        )

        missing.parent.mkdir(parents=True)
        missing.write_bytes(b"x")
        assert check_master_file_exists(missing).passed is True

    def test_master_playable(self, tmp_path: Path) -> None:
        mp3 = tmp_path / "narration_master.mp3"
        mp3.write_bytes(b"x")
        bad = check_master_playable(mp3, probe=lambda p: 0.0)
        assert bad.passed is False
        assert "duration" in bad.reason.lower()

        good = check_master_playable(mp3, probe=lambda p: 1.23)
        assert good.passed is True

    def test_concat_integrity(self, happy_path_project) -> None:
        _, project_root, _, durations = happy_path_project
        phase_dir = project_root / "phase_4"
        ok = check_concat_integrity(
            timeline_path=phase_dir / "timeline.json",
            phase_dir=phase_dir,
            master_path=phase_dir / "narration_master.mp3",
            probe=_fake_probe(durations),
        )
        assert ok.passed is True, ok.reason

        bad_durations = dict(durations)
        bad_durations[phase_dir / "seg_02.mp3"] = 0.4  # 100ms drift
        bad = check_concat_integrity(
            timeline_path=phase_dir / "timeline.json",
            phase_dir=phase_dir,
            master_path=phase_dir / "narration_master.mp3",
            probe=_fake_probe(bad_durations),
        )
        assert bad.passed is False
        assert (
            "concat" in bad.reason.lower()
            or "drift" in bad.reason.lower()
            or "diff" in bad.reason.lower()
        )

    def test_checksum_consistent(self, tmp_path: Path) -> None:
        mp3 = tmp_path / "narration_master.mp3"
        mp3.write_bytes(b"hello-world")
        real = _sha256(mp3)
        assert check_checksum_consistent(mp3, real).passed is True
        wrong = "sha256:" + "0" * 64
        bad = check_checksum_consistent(mp3, wrong)
        assert bad.passed is False
        assert "checksum" in bad.reason.lower()

    def test_master_audio_ref_switched(self, happy_path_project) -> None:
        project_id, _, conn, _ = happy_path_project
        good = check_master_audio_ref_switched(conn, project_id)
        assert good.passed is True

        conn.execute(
            "UPDATE projects SET master_audio_ref = ? WHERE project_id = ?",
            (json.dumps({"kind": "bgm_mix_master"}), project_id),
        )
        conn.commit()
        bad = check_master_audio_ref_switched(conn, project_id)
        assert bad.passed is False
        assert "narration_master" in bad.reason

        conn.execute(
            "UPDATE projects SET master_audio_ref = NULL WHERE project_id = ?",
            (project_id,),
        )
        conn.commit()
        assert check_master_audio_ref_switched(conn, project_id).passed is False


# ---------- AC-2 -------------------------------------------------


class TestAC2:
    """Missing segment -> concat FAIL -> Gate FAIL; others PASS (no bypass)."""

    def test_missing_segment_fails_gate(self, happy_path_project) -> None:
        project_id, project_root, conn, durations = happy_path_project
        phase_dir = project_root / "phase_4"
        (phase_dir / "seg_02.mp3").unlink()

        checker = GateP4Checker(conn, probe=_fake_probe(durations))
        result = checker.check(project_id, project_root)

        assert result.passed is False
        by_name = {c.check: c for c in result.new_checks}
        assert by_name["concat_integrity"].passed is False
        assert by_name["master_exists"].passed is True
        assert by_name["master_playable"].passed is True
        assert by_name["checksum_consistent"].passed is True
        assert by_name["master_audio_ref_switched"].passed is True


# ---------- AC-3 -------------------------------------------------


class TestAC3:
    """v3.15 Gate-P4 7-item gate still PASS end-to-end."""

    def test_v315_regression_all_pass(self, happy_path_project) -> None:
        project_id, project_root, conn, durations = happy_path_project
        checker = GateP4Checker(conn, probe=_fake_probe(durations))
        result = checker.check(project_id, project_root)

        v315_names = {c.check for c in result.v315_checks}
        expected = {
            "artifact_exists",
            "version_match",
            "review_passed",
            "no_running_tasks",
            "no_running_async_tasks",
            "preferences_confirmed",
            "cost_logged",
        }
        assert expected.issubset(v315_names)
        for c in result.v315_checks:
            assert c.passed, f"v3.15 regression {c.check} failed: {c.reason}"


# ---------- AC-5 -------------------------------------------------


class TestAC5:
    """Report lists 5 v3.17 checks + N v3.15 checks with verdict/reason."""

    def test_gate_report_structure(self, happy_path_project) -> None:
        project_id, project_root, conn, durations = happy_path_project
        checker = GateP4Checker(conn, probe=_fake_probe(durations))
        result = checker.check(project_id, project_root)

        assert isinstance(result, GateP4Result)
        assert {c.check for c in result.new_checks} == {
            "master_exists",
            "master_playable",
            "concat_integrity",
            "checksum_consistent",
            "master_audio_ref_switched",
        }
        assert len(result.v315_checks) >= 6

        for c in [*result.new_checks, *result.v315_checks]:
            assert isinstance(c.check, str) and c.check
            assert isinstance(c.passed, bool)
            assert isinstance(c.reason, str)

        all_new_ok = all(c.passed for c in result.new_checks)
        all_v315_ok = all(c.passed for c in result.v315_checks)
        assert result.passed == (all_new_ok and all_v315_ok)
