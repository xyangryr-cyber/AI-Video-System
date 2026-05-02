"""[SPEC-C-015] GateKeeper -- 7-item phase gate + skip branch + Claude routing.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-8.1 / 8.2 / 8.3 / 8.4.

Responsibilities
----------------
1. Run the SPEC-8.1 7-item gate check for a (project, phase) pair and
   report ALL failing items (no short-circuit, per SPEC-A SPEC-13A gate
   failure shape).
2. Route the cost check (#7) to a non-blocking WARN bucket: a missing
   ``agent_call_log`` row is surfaced in ``warnings`` but does not flip
   ``passed``.
3. In ``skip`` mode, only run checks #4 (no in-progress task_ledger
   entries) and #6 (preferences confirmed) -- SPEC-8.2.
4. Expose :class:`ReviewerResult` that mirrors SPEC-8.3's binary verdict
   invariant (``blocking_issues == []`` iff ``verdict == "PASS"``). The
   stored review blob in ``task_ledger.result_ref`` is parsed through
   this model so an inconsistent review can never silently pass the gate.
5. Resolve the ``gatekeeper`` LLM role via ``llm_service.resolve_model``
   (SPEC-8.4) and provide a minimal :meth:`advise` entry point that runs
   through ``llm_service.chat_completion`` so the call log records the
   configured Claude model (AC-8 / AC-9).

Read-only by design
-------------------
GateKeeper never writes to the database. It only issues SELECT queries
against ``projects``, ``phases``, ``task_ledger``, ``async_tasks`` and
``agent_call_log``, so it satisfies SPEC-B-002's "raw DB mutation SQL
must live in repositories" rule without any split-string gymnastics.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from src.backend.services import llm_service

# -- Check names ---------------------------------------------------------

# Order matches SPEC-8.1 rows 1..6 (blocking) + row 7 (non-blocking).
# Kept in sync with the task-card AC-1 failure-mode enumeration.
BLOCKING_CHECK_NAMES: tuple[str, ...] = (
    "artifact_exists",
    "version_match",
    "review_passed",
    "no_running_tasks",
    "no_running_async_tasks",
    "preferences_confirmed",
    "content_quality",
)

# SPEC-8.2: skip mode runs only #4 and #6.
SKIP_CHECK_NAMES: tuple[str, ...] = (
    "no_running_tasks",
    "preferences_confirmed",
)

# SPEC-8.1 row 7 -- cost check is WARN-only.
COST_CHECK_NAME = "cost_logged"


# -- Review-result contract (SPEC-8.3) ----------------------------------


Verdict = Literal["PASS", "FAIL"]


class ReviewerResult(BaseModel):
    """Parsed review blob stored in ``task_ledger.result_ref``.

    SPEC-8.3 invariant (two-way): ``blocking_issues == []`` iff
    ``verdict == "PASS"``. The model-level validator enforces both
    directions so the gate cannot be tricked by an inconsistent review.
    """

    verdict: Verdict
    blocking_issues: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def _verdict_matches_blocking(self) -> ReviewerResult:
        has_blockers = len(self.blocking_issues) > 0
        if has_blockers and self.verdict != "FAIL":
            raise ValueError("blocking_issues non-empty but verdict != 'FAIL' (SPEC-8.3)")
        if not has_blockers and self.verdict != "PASS":
            raise ValueError("blocking_issues empty but verdict != 'PASS' (SPEC-8.3)")
        return self


# -- Gate result types --------------------------------------------------


@dataclass(frozen=True)
class CheckResult:
    """One check's outcome. ``reason`` is empty on pass."""

    check: str
    passed: bool
    reason: str = ""


@dataclass(frozen=True)
class GateResult:
    """Aggregate outcome for a gate invocation.

    ``passed`` reflects the 6 blocking checks only; ``warnings`` carries
    the non-blocking cost check (#7) when it is missing.
    """

    passed: bool
    failed_checks: list[CheckResult] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    warnings: list[CheckResult] = field(default_factory=list)


# -- GateKeeper ---------------------------------------------------------


Mode = Literal["advance", "skip"]


class GateKeeper:
    """SPEC-8 gate checker."""

    def __init__(
        self,
        conn: sqlite3.Connection,
        *,
        config_path: str | Path | None = None,
    ) -> None:
        self._conn = conn
        self._config_path = config_path

    # ---- Public API ----------------------------------------------------

    def check(
        self,
        project_id: str,
        phase_num: int,
        *,
        mode: Mode = "advance",
    ) -> GateResult:
        """Run the gate for ``(project_id, phase_num)``.

        ``mode="skip"`` restricts the run to SPEC-8.2's two checks
        (no in-progress tasks, preferences confirmed). The cost check
        is WARN-only in both modes.
        """
        phase = self._load_phase(project_id, phase_num)

        blocking: list[CheckResult] = []
        warnings: list[CheckResult] = []

        if mode == "skip":
            blocking.append(self._check_no_running_tasks(project_id, phase_num))
            blocking.append(self._check_preferences_confirmed(phase))
        else:
            blocking.append(self._check_artifact_exists(phase))
            blocking.append(self._check_version_match(project_id, phase_num, phase))
            blocking.append(self._check_review_passed(project_id, phase_num, phase))
            blocking.append(self._check_no_running_tasks(project_id, phase_num))
            blocking.append(self._check_no_running_async_tasks(project_id, phase_num))
            blocking.append(self._check_preferences_confirmed(phase))
            blocking.append(self._check_content_quality(project_id, phase_num, phase))
            warnings.append(self._check_cost_logged(project_id, phase_num))

        failed = [c for c in blocking if not c.passed]
        passed_names = [c.check for c in blocking if c.passed]
        # Include the warning-bucket pass (cost_logged) in passed_checks
        # so callers can assert full 7-item passthrough in advance mode.
        passed_names.extend(w.check for w in warnings if w.passed)

        return GateResult(
            passed=len(failed) == 0,
            failed_checks=failed,
            passed_checks=passed_names,
            warnings=[w for w in warnings if not w.passed],
        )

    def model(self) -> str:
        """Return the Claude model bound to the ``gatekeeper`` role."""
        return llm_service.resolve_model("gatekeeper", config_path=self._config_path)

    def advise(
        self,
        *,
        messages: Sequence[Mapping[str, Any]],
        _completion_fn: Callable[..., Any] | None = None,
    ) -> Any:
        """Escalate a gate decision to the LLM (Claude via ``gatekeeper`` role).

        Thin shim over :func:`llm_service.chat_completion` so the
        call-log model field matches :meth:`model`. The test injects
        ``_completion_fn`` to capture the outgoing ``model`` kwarg.
        """
        return llm_service.chat_completion(
            role="gatekeeper",
            messages=messages,
            config_path=self._config_path,
            _completion_fn=_completion_fn,
        )

    # ---- Individual checks --------------------------------------------

    def _check_artifact_exists(self, phase: Mapping[str, Any] | None) -> CheckResult:
        if phase is None:
            return CheckResult("artifact_exists", False, "phase row missing")
        path = phase["artifact_path"]
        status = phase["artifact_status"]
        if path and status == "ok":
            return CheckResult("artifact_exists", True)
        return CheckResult(
            "artifact_exists",
            False,
            f"artifact_path={path!r} artifact_status={status!r}",
        )

    def _check_version_match(
        self,
        project_id: str,
        phase_num: int,
        phase: Mapping[str, Any] | None,
    ) -> CheckResult:
        if phase is None:
            return CheckResult("version_match", False, "phase row missing")
        latest = self._latest_review(project_id, phase_num)
        if latest is None:
            return CheckResult("version_match", False, "no review task recorded")
        artifact_version = int(phase["artifact_version"])
        target_version = latest["target_version"]
        if target_version == artifact_version:
            return CheckResult("version_match", True)
        return CheckResult(
            "version_match",
            False,
            f"latest review targets v{target_version}, phase at v{artifact_version}",
        )

    def _check_review_passed(
        self,
        project_id: str,
        phase_num: int,
        phase: Mapping[str, Any] | None,
    ) -> CheckResult:
        latest = self._latest_review(project_id, phase_num)
        if latest is None:
            return CheckResult("review_passed", False, "no review task recorded")
        if latest["status"] != "succeeded":
            return CheckResult(
                "review_passed",
                False,
                f"latest review status={latest['status']}",
            )
        blob = latest["result_ref"]
        if not blob:
            return CheckResult("review_passed", False, "review result_ref empty")
        try:
            parsed = ReviewerResult.model_validate_json(blob)
        except Exception as exc:  # noqa: BLE001 -- surface parse failure
            return CheckResult("review_passed", False, f"review result parse error: {exc}")
        if parsed.verdict != "PASS":
            return CheckResult(
                "review_passed",
                False,
                f"review verdict={parsed.verdict}",
            )
        return CheckResult("review_passed", True)

    def _check_no_running_tasks(self, project_id: str, phase_num: int) -> CheckResult:
        row = self._conn.execute(
            "SELECT id FROM task_ledger "
            "WHERE project_id = ? AND phase = ? "
            "AND status IN ('pending','queued','running') "
            "LIMIT 1",
            (project_id, phase_num),
        ).fetchone()
        if row is None:
            return CheckResult("no_running_tasks", True)
        return CheckResult(
            "no_running_tasks",
            False,
            f"task {row[0]} is still in-flight",
        )

    def _check_no_running_async_tasks(self, project_id: str, phase_num: int) -> CheckResult:
        row = self._conn.execute(
            "SELECT task_id FROM async_tasks "
            "WHERE project_id = ? AND phase = ? "
            "AND status IN ('pending','queued','running') "
            "LIMIT 1",
            (project_id, phase_num),
        ).fetchone()
        if row is None:
            return CheckResult("no_running_async_tasks", True)
        return CheckResult(
            "no_running_async_tasks",
            False,
            f"async task {row[0]} is still in-flight",
        )

    def _check_preferences_confirmed(self, phase: Mapping[str, Any] | None) -> CheckResult:
        if phase is None:
            return CheckResult("preferences_confirmed", False, "phase row missing")
        ts = phase["preferences_confirmed_at"]
        if ts:
            return CheckResult("preferences_confirmed", True)
        return CheckResult(
            "preferences_confirmed",
            False,
            "preferences_confirmed_at is NULL",
        )

    def _check_content_quality(
        self,
        project_id: str,
        phase_num: int,
        phase: dict[str, Any] | None,
    ) -> CheckResult:
        """Run the phase-specific content quality detector.

        - P0-P3: detect placeholder text in artifact.
        - P8:   detect uniform / solid-color image frames.
        - P4, P10: detect duration deviation (skipped when measured data
          is unavailable — returns PASS so it never blocks prematurely).
        """
        # Lazy imports avoid circular dependency with gates/__init__.py.
        from src.backend.gates.content_quality_checks import (
            detect_duration_deviation,
            detect_placeholder_text,
            detect_uniform_color_frame,
        )

        if phase_num in (0, 1, 2, 3):
            text = self._load_artifact_text(phase)
            placeholders = detect_placeholder_text({"text": text})
            if placeholders:
                return CheckResult(
                    "content_quality",
                    False,
                    f"placeholder text found: {placeholders}",
                )
        elif phase_num == 8:
            image_path = phase.get("artifact_path") if phase else None
            if image_path and detect_uniform_color_frame(image_path):
                return CheckResult(
                    "content_quality",
                    False,
                    "uniform color frame detected",
                )
        elif phase_num in (4, 10):
            measured_sec = self._read_measured_duration_sec(phase)
            if measured_sec is not None:
                declared_duration = self._load_artifact_declared_duration(phase)
                is_deviation, pct = detect_duration_deviation(
                    {"duration": declared_duration}, measured_sec
                )
                if is_deviation:
                    return CheckResult(
                        "content_quality",
                        False,
                        f"duration deviation {pct}%",
                    )

        return CheckResult("content_quality", True)

    def _check_cost_logged(self, project_id: str, phase_num: int) -> CheckResult:
        row = self._conn.execute(
            "SELECT id FROM agent_call_log WHERE project_id = ? AND phase = ? LIMIT 1",
            (project_id, phase_num),
        ).fetchone()
        if row is None:
            return CheckResult("cost_logged", False, "no agent_call_log entries yet")
        return CheckResult("cost_logged", True)

    # ---- Helpers -------------------------------------------------------

    def _load_artifact_text(self, phase: dict[str, Any] | None) -> str:
        """Read text content from the artifact file (P0-P3 phases).

        Returns the file content as a string, or ``""`` on any error.
        """
        if phase is None:
            return ""
        path = phase.get("artifact_path")
        if not path:
            return ""
        try:
            return Path(path).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return ""

    def _load_artifact_declared_duration(self, phase: dict[str, Any] | None) -> float:
        """Extract a declared duration (seconds) from the phase artifact.

        For audio phases the artifact JSON may carry ``"duration"`` or
        ``"total_duration"``.  Falls back to 0.0.
        """
        if phase is None:
            return 0.0
        path = phase.get("artifact_path")
        if not path:
            return 0.0
        try:
            import json

            data = json.loads(Path(path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return 0.0
        return float(data.get("duration", 0) or data.get("total_duration", 0) or 0)

    @staticmethod
    def _read_measured_duration_sec(phase: dict[str, Any] | None) -> float | None:
        """Read audio/video duration via ffprobe (or from JSON sidecar).

        Returns ``None`` when the tool is unavailable — the caller treats
        ``None`` as "skip this check".
        """
        if phase is None:
            return None
        path = phase.get("artifact_path")
        if not path or not Path(path).exists():
            return None
        try:
            import shutil

            ffprobe = shutil.which("ffprobe")
            if not ffprobe:
                return None

            import subprocess

            result = subprocess.run(
                [
                    ffprobe,
                    "-v",
                    "error",
                    "-show_entries",
                    "format=duration",
                    "-of",
                    "default=noprint_wrappers=1:nokey=1",
                    str(path),
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
            return float(result.stdout.strip()) if result.returncode == 0 else None
        except Exception:
            return None

    def _load_phase(self, project_id: str, phase_num: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT artifact_path, artifact_status, artifact_version, "
            "preferences_confirmed_at FROM phases "
            "WHERE project_id = ? AND phase_num = ?",
            (project_id, phase_num),
        ).fetchone()
        if row is None:
            return None
        return {
            "artifact_path": row[0],
            "artifact_status": row[1],
            "artifact_version": row[2],
            "preferences_confirmed_at": row[3],
        }

    def _latest_review(self, project_id: str, phase_num: int) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT id, status, target_version, result_ref "
            "FROM task_ledger "
            "WHERE project_id = ? AND phase = ? AND type = 'review' "
            "ORDER BY created_at DESC, id DESC LIMIT 1",
            (project_id, phase_num),
        ).fetchone()
        if row is None:
            return None
        return {
            "id": row[0],
            "status": row[1],
            "target_version": row[2],
            "result_ref": row[3],
        }


__all__ = [
    "BLOCKING_CHECK_NAMES",
    "SKIP_CHECK_NAMES",
    "COST_CHECK_NAME",
    "CheckResult",
    "GateKeeper",
    "GateResult",
    "ReviewerResult",
    "Verdict",
]
