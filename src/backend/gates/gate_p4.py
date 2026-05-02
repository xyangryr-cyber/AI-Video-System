"""[SPEC-D-018] Gate-P4 v3.17 upgrade.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §D-AUDP7A-1.

``GateP4Checker`` layers 5 new v3.17 audio checks on top of the v3.15
7-item SPEC-8 ``GateKeeper`` without removing or weakening any existing
assertion:

* master_exists            -- narration_master.mp3 + .json on disk
* master_playable          -- ffprobe duration > 0 on master
* concat_integrity         -- sum(segment.duration) == master.duration (+/- 50 ms)
* checksum_consistent      -- recomputed sha256(master.mp3) matches json.checksum
* master_audio_ref_switched -- projects.master_audio_ref.kind == "narration_master"

All 5 checks run unconditionally (no short-circuit) so AC-2's
"other four still PASS, not bypassed" contract holds even when one of
them FAILs. The aggregate :class:`GateP4Result` surfaces both buckets
(v3.17 + v3.15) so callers render a single unified report.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from src.backend.engine.gatekeeper import (
    CheckResult,
    GateKeeper,
    GateResult,
)
from src.backend.gates.audio_master_checks import (
    ProbeFn,
    check_checksum_consistent,
    check_master_file_exists,
    check_master_playable,
    ffprobe_duration_seconds,
)


# Tolerance for concat-integrity sum-of-segment durations (v3.17 AC-1).
DEFAULT_CONCAT_TOLERANCE_SECONDS: float = 0.050  # 50 ms


@dataclass(frozen=True)
class GateP4Result:
    """Gate-P4 aggregate report (v3.17 + v3.15 check buckets)."""

    passed: bool
    new_checks: list[CheckResult] = field(default_factory=list)
    v315_checks: list[CheckResult] = field(default_factory=list)


__all__ = [
    "DEFAULT_CONCAT_TOLERANCE_SECONDS",
    "GateP4Checker",
    "GateP4Result",
    "check_concat_integrity",
    "check_master_audio_ref_switched",
]


# ---------------------------------------------------------------------
# Individual v3.17 checks (module-level so Gate-P5/P6 callers can reuse).
# ---------------------------------------------------------------------


def check_concat_integrity(
    *,
    timeline_path: Path,
    phase_dir: Path,
    master_path: Path,
    probe: ProbeFn | None = None,
    tolerance_seconds: float = DEFAULT_CONCAT_TOLERANCE_SECONDS,
) -> CheckResult:
    """sum(segment durations) ~= master duration within ``tolerance_seconds``.

    ``probe`` lets unit tests inject synthetic durations (avoids ffprobe
    dependency); production code defaults to the shared ffprobe helper.
    """
    fn = probe or ffprobe_duration_seconds
    tp = Path(timeline_path)
    if not tp.is_file():
        return CheckResult("concat_integrity", False, f"timeline.json not found: {tp}")
    try:
        timeline = json.loads(tp.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return CheckResult(
            "concat_integrity", False, f"timeline.json unreadable: {exc}"
        )
    segments = timeline.get("segments")
    if not isinstance(segments, list) or not segments:
        return CheckResult(
            "concat_integrity", False, "timeline.segments empty or missing"
        )

    sum_seg = 0.0
    for i, seg in enumerate(segments):
        if not isinstance(seg, dict):
            return CheckResult(
                "concat_integrity",
                False,
                f"segment #{i} is not an object",
            )
        audio_path = seg.get("audio_path")
        if not isinstance(audio_path, str) or not audio_path:
            return CheckResult(
                "concat_integrity",
                False,
                f"segment #{i} missing audio_path",
            )
        seg_path = _resolve_segment_path(phase_dir, audio_path)
        if not seg_path.is_file():
            return CheckResult(
                "concat_integrity",
                False,
                f"segment file missing: {seg_path}",
            )
        try:
            sum_seg += float(fn(seg_path))
        except Exception as exc:  # noqa: BLE001
            return CheckResult(
                "concat_integrity",
                False,
                f"probe failed on {seg_path}: {exc}",
            )

    try:
        master_dur = float(fn(Path(master_path)))
    except Exception as exc:  # noqa: BLE001
        return CheckResult(
            "concat_integrity",
            False,
            f"probe failed on master: {exc}",
        )

    diff = abs(sum_seg - master_dur)
    if diff > tolerance_seconds:
        return CheckResult(
            "concat_integrity",
            False,
            (
                f"concat drift: sum(segments)={sum_seg:.3f}s "
                f"master={master_dur:.3f}s "
                f"diff={diff * 1000:.1f}ms > tolerance "
                f"{tolerance_seconds * 1000:.1f}ms"
            ),
        )
    return CheckResult("concat_integrity", True)


def check_master_audio_ref_switched(
    conn: sqlite3.Connection, project_id: str
) -> CheckResult:
    """``projects.master_audio_ref.kind`` must be ``narration_master``."""
    row = conn.execute(
        "SELECT master_audio_ref FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    if row is None:
        return CheckResult(
            "master_audio_ref_switched",
            False,
            f"project {project_id!r} not found",
        )
    raw = row[0] if not hasattr(row, "keys") else row["master_audio_ref"]
    if raw is None:
        return CheckResult(
            "master_audio_ref_switched",
            False,
            "master_audio_ref is NULL -- expected kind=narration_master",
        )
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        return CheckResult(
            "master_audio_ref_switched",
            False,
            f"master_audio_ref is not valid JSON: {exc}",
        )
    kind = payload.get("kind") if isinstance(payload, dict) else None
    if kind != "narration_master":
        return CheckResult(
            "master_audio_ref_switched",
            False,
            (f"master_audio_ref.kind must be 'narration_master', got {kind!r}"),
        )
    return CheckResult("master_audio_ref_switched", True)


# ---------------------------------------------------------------------


class GateP4Checker:
    """Run 5 v3.17 checks + the 7-item v3.15 SPEC-8 gate, aggregate the results.

    The v3.15 bucket is delegated to the generic ``GateKeeper`` (SPEC-8)
    so any future regression there surfaces here automatically -- this
    is the "既有断言不删不改" invariant from the task card's forbidden
    files list.

    Also provides the simpler D-004 AC-11 gate interface (check_p4_gate)
    for phase-advance gating before the v3.17 audio-master layer exists.
    """

    def __init__(
        self,
        conn: sqlite3.Connection | None = None,
        *,
        config_path: str | Path | None = None,
        probe: ProbeFn | None = None,
        check_audio_files_exist: Any = None,
    ) -> None:
        self._conn = conn
        self._gatekeeper = GateKeeper(conn, config_path=config_path) if conn else None
        self._probe = probe
        # Allow test-injected check function for D-004 AC-11
        self._check_audio_files_exist = check_audio_files_exist

    @staticmethod
    def check_p4_gate(
        *,
        audio_files_exist: bool,
        reviewer_passed: bool,
        async_task_done: bool,
        pending_tasks: list[Any],
        preferences_confirmed: bool,
    ) -> dict[str, Any]:
        """Simple gate check for D-004 AC-11. Does not require DB/file access."""
        failed: list[str] = []
        passed: list[str] = []

        if not audio_files_exist:
            failed.append("segment audio files missing or not playable")
        else:
            passed.append("audio files exist and playable")

        if not reviewer_passed:
            failed.append("AudioQualityReviewer FAIL")
        else:
            passed.append("AudioQualityReviewer PASS")

        if not async_task_done:
            failed.append("TTS async_task not done")
        else:
            passed.append("async_task done")

        if pending_tasks:
            failed.append(f"{len(pending_tasks)} pending tasks remain")
        else:
            passed.append("no pending tasks")

        if not preferences_confirmed:
            failed.append("preferences not confirmed")
        else:
            passed.append("preferences confirmed")

        return {
            "passed": len(failed) == 0,
            "failed_checks": failed,
            "passed_checks": passed,
        }

    def check(
        self,
        project_id: str,
        project_root: Path,
        *,
        master_stem: str = "narration_master",
    ) -> GateP4Result:
        """Run all 5 v3.17 checks + the v3.15 7-item gate for phase 4."""
        phase_dir = Path(project_root) / "phase_4"
        master_mp3 = phase_dir / f"{master_stem}.mp3"
        master_json = phase_dir / f"{master_stem}.json"
        timeline_path = phase_dir / "timeline.json"

        # ----- v3.17 bucket (unconditional, no short-circuit) -------
        r_exists = check_master_file_exists(master_mp3)
        r_playable = check_master_playable(master_mp3, probe=self._probe)
        r_concat = check_concat_integrity(
            timeline_path=timeline_path,
            phase_dir=phase_dir,
            master_path=master_mp3,
            probe=self._probe,
        )
        r_checksum = self._run_checksum_check(master_mp3, master_json)
        r_ref = check_master_audio_ref_switched(
            cast(sqlite3.Connection, self._conn), project_id
        )
        new_checks: list[CheckResult] = [
            r_exists,
            r_playable,
            r_concat,
            r_checksum,
            r_ref,
        ]

        # ----- v3.15 bucket (delegated; unchanged) ------------------
        if self._gatekeeper is None:
            v315 = GateResult(
                passed=False,
                failed_checks=[
                    CheckResult(
                        check="gatekeeper",
                        passed=False,
                        reason="gatekeeper not initialized",
                    )
                ],
                passed_checks=[],
            )
        else:
            v315 = self._gatekeeper.check(project_id, 4, mode="advance")
        v315_checks = _flatten_gate_result(v315)

        all_new_ok = all(c.passed for c in new_checks)
        all_v315_ok = all(c.passed for c in v315_checks)
        return GateP4Result(
            passed=all_new_ok and all_v315_ok,
            new_checks=new_checks,
            v315_checks=v315_checks,
        )

    # ---- helpers -----------------------------------------------

    @staticmethod
    def _run_checksum_check(master_mp3: Path, master_json: Path) -> CheckResult:
        if not master_json.is_file():
            return CheckResult(
                "checksum_consistent",
                False,
                f"narration_master.json missing: {master_json}",
            )
        try:
            side_car = json.loads(master_json.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return CheckResult(
                "checksum_consistent",
                False,
                f"narration_master.json unreadable: {exc}",
            )
        expected = side_car.get("checksum")
        if not isinstance(expected, str):
            return CheckResult(
                "checksum_consistent",
                False,
                "narration_master.json missing 'checksum' field",
            )
        if not master_mp3.is_file():
            return CheckResult(
                "checksum_consistent",
                False,
                f"master mp3 missing: {master_mp3}",
            )
        return check_checksum_consistent(master_mp3, expected)


# ---------------------------------------------------------------------


def _resolve_segment_path(phase_dir: Path, audio_path: str) -> Path:
    """Mirror NarrationMasterAssembler segment resolution semantics."""
    project_root = phase_dir.parent
    candidate = (project_root / audio_path).resolve()
    if candidate.exists():
        return candidate
    # Fallback: audio_path leaf inside phase_dir.
    return (phase_dir / Path(audio_path).name).resolve()


def _flatten_gate_result(result: GateResult) -> list[CheckResult]:
    """Rebuild per-check CheckResult list from a GateKeeper GateResult.

    GateResult collapses PASS entries to a name list; Gate-P4 needs a
    full (check, passed, reason) tuple for every v3.15 check so AC-5's
    report structure invariant ("含 N 项 v3.15 检查的明细 verdict 与 reason")
    holds regardless of pass/fail shape.
    """
    flat: list[CheckResult] = []
    seen: set[str] = set()
    for name in result.passed_checks:
        flat.append(CheckResult(name, True))
        seen.add(name)
    for c in result.failed_checks:
        if c.check in seen:
            continue
        flat.append(c)
        seen.add(c.check)
    for c in result.warnings:
        if c.check in seen:
            continue
        flat.append(c)
        seen.add(c.check)
    return flat
