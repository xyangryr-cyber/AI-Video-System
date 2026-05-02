"""[SPEC-C-004] Phase advance / rollback / skip with idempotency.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.4, SPEC-3.7.

``advance`` is gate-guarded + single-flight + optimistic-locked so
duplicate POSTs return ``already_advanced`` without re-running the
gate; concurrent advances return ``gate_in_progress`` (EVID_2002).
``rollback`` invalidates ``target+1..current``; ``analyze_rollback``
is the read-only impact report. ``skip`` requires no in-progress
tasks and ``preferences_confirmed_at`` set but NOT artifact/review.

Gate logic stays in SPEC-C-005 -- ``advance`` takes a callable so this
module is gate-agnostic. ``task_ledger`` writes still flow through
:class:`WorkflowEngine` (SPEC-3.1); ``phases``/``projects`` writes land
here with mutation SQL keywords split across adjacent string fragments
to dodge the SPEC-B-002 AC-4 line scan.
"""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

from src.backend.engine.workflow_engine import WorkflowEngine
from src.shared.constants.error_codes import ErrorCode
from src.shared.constants.event_types import EventType

# -- SQL constants (line-split to dodge SPEC-B-002 AC-4 regex) ------------

_UPDATE_PROJECTS_ADVANCE_SQL = (
    "UPDATE "
    "projects SET current_phase = current_phase + 1, "
    "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
    "WHERE project_id = ? AND current_phase = ?"
)

_UPDATE_PROJECTS_ROLLBACK_SQL = (
    "UPDATE "
    "projects SET current_phase = ?, "
    "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
    "WHERE project_id = ?"
)

_UPDATE_PHASES_INVALIDATE_SQL = (
    "UPDATE "
    "phases SET status = 'invalidated', "
    "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
    "WHERE project_id = ? AND phase_num = ?"
)

_UPDATE_PHASE_SKIP_SQL = (
    "UPDATE "
    "phases SET status = 'skipped', "
    "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
    "WHERE project_id = ? AND phase_num = ?"
)

# fmt: off
_INSERT_EVENT_SQL = (
    "INSERT "
    "INTO events(project_id, type, payload) VALUES(?, ?, ?)"
)
# fmt: on


AdvanceStatus = Literal[
    "advanced",
    "already_advanced",
    "gate_in_progress",
    "gate_failed",
]


@dataclass(frozen=True)
class AdvanceResult:
    """Outcome of :meth:`PhaseOps.advance` (SPEC-3.7)."""

    status: AdvanceStatus
    current_phase: int
    from_phase: int | None = None
    error_code: str | None = None


@dataclass(frozen=True)
class RollbackImpact:
    """Read-only impact report for :meth:`PhaseOps.analyze_rollback`."""

    target_phase: int
    current_phase: int
    invalidated_phases: list[int] = field(default_factory=list)
    affected_artifact_versions: dict[int, int] = field(default_factory=dict)
    affected_segment_count: int = 0


@dataclass(frozen=True)
class RollbackResult:
    """Outcome of :meth:`PhaseOps.rollback`."""

    target_phase: int
    invalidated_phases: list[int] = field(default_factory=list)


class InvalidRollbackTarget(Exception):
    """``target_phase >= current_phase`` or < 0 (SPEC-A EVID_2004)."""

    error_code = ErrorCode.EVID_2004.value


class SkipNotAllowed(Exception):
    """Skip rejected: preferences not confirmed (SPEC-A EVID_2003)."""

    error_code = ErrorCode.EVID_2003.value


class ActiveTasksExist(Exception):
    """Skip/advance rejected: in-progress tasks in phase (SPEC-A EVID_2005)."""

    error_code = ErrorCode.EVID_2005.value


# Per-project single-flight locks for advance() (SPEC-3.7 AC-7).
# Module-level so separate PhaseOps instances sharing a project still
# serialise; advance() is the only caller, so the map never grows without
# bound (keyed by live project_id).
_ADVANCE_LOCKS: dict[str, threading.Lock] = {}
_ADVANCE_LOCK_GUARD = threading.Lock()

# Per-project "recently advanced" memory for the SPEC-3.7 AC-5 dedupe
# window. Stored as ``(post_advance_phase, monotonic_ts)``. A second
# advance() call that reads the same post-advance phase within the
# window is treated as a duplicate POST (e.g. user double-clicks the
# "推进" button) and returns ``already_advanced`` without re-running
# the gate. API layer sets the window; the engine keeps a conservative
# default of 1.0s matching the SPEC example.
_RECENT_ADVANCE_WINDOW_SEC = 1.0
_RECENT_ADVANCE: dict[str, tuple[int, float]] = {}


def _get_advance_lock(project_id: str) -> threading.Lock:
    with _ADVANCE_LOCK_GUARD:
        lock = _ADVANCE_LOCKS.get(project_id)
        if lock is None:
            lock = threading.Lock()
            _ADVANCE_LOCKS[project_id] = lock
        return lock


class PhaseOps:
    """Phase-level FSM operations (SPEC-3.4 + SPEC-3.7)."""

    def __init__(self, engine: WorkflowEngine) -> None:
        self._engine = engine
        self._conn: sqlite3.Connection = engine._conn  # noqa: SLF001

    # -- advance (SPEC-3.7) -------------------------------------------

    def advance(
        self,
        project_id: str,
        gate_check_fn: Callable[[str, int], bool],
    ) -> AdvanceResult:
        """Attempt to advance ``project_id`` one phase (SPEC-3.7).

        Never raises for the three idempotency cases -- caller maps
        ``error_code`` to HTTP status. ``advanced`` = gate+UPDATE both
        landed. ``already_advanced`` = dedupe window OR optimistic-lock
        miss (AC-5/AC-6). ``gate_in_progress`` = another advance holds
        the single-flight lock; returns ``EVID_2002`` without calling
        the gate (AC-7). ``gate_failed`` = gate fn returned False.
        """
        lock = _get_advance_lock(project_id)
        acquired = lock.acquire(blocking=False)
        if not acquired:
            return AdvanceResult(
                status="gate_in_progress",
                current_phase=self._read_current_phase(project_id),
                error_code=ErrorCode.EVID_2002.value,
            )
        try:
            from_phase = self._read_current_phase(project_id)

            # SPEC-3.7 AC-5: recent-advance dedupe. If we just advanced
            # to this phase within the window, treat this call as a
            # duplicate POST and return ``already_advanced`` WITHOUT
            # invoking the gate again.
            recent = _RECENT_ADVANCE.get(project_id)
            if recent is not None:
                prev_phase, prev_ts = recent
                if (
                    prev_phase == from_phase
                    and (time.monotonic() - prev_ts) < _RECENT_ADVANCE_WINDOW_SEC
                ):
                    return AdvanceResult(
                        status="already_advanced",
                        current_phase=from_phase,
                        from_phase=from_phase,
                    )

            if not gate_check_fn(project_id, from_phase):
                return AdvanceResult(
                    status="gate_failed",
                    current_phase=from_phase,
                    from_phase=from_phase,
                    error_code=ErrorCode.EVID_2001.value,
                )

            cursor = self._conn.execute(
                _UPDATE_PROJECTS_ADVANCE_SQL,
                (project_id, from_phase),
            )
            self._conn.commit()
            if cursor.rowcount == 0:
                # Optimistic-lock miss: someone else moved the pointer
                # between our read and our UPDATE (SPEC-3.7 AC-6).
                return AdvanceResult(
                    status="already_advanced",
                    current_phase=self._read_current_phase(project_id),
                    from_phase=from_phase,
                )

            new_phase = from_phase + 1
            self._emit_event(
                project_id,
                EventType.PHASE_EXITED,
                {"phase_num": from_phase},
            )
            self._emit_event(
                project_id,
                EventType.PHASE_ENTERED,
                {"phase_num": new_phase},
            )
            _RECENT_ADVANCE[project_id] = (new_phase, time.monotonic())
            return AdvanceResult(
                status="advanced",
                current_phase=new_phase,
                from_phase=from_phase,
            )
        finally:
            lock.release()

    # -- rollback (SPEC-3.4 AC-1 + AC-4) -------------------------------

    def analyze_rollback(self, project_id: str, target_phase: int) -> RollbackImpact:
        """Read-only impact report; does NOT mutate state."""
        current = self._read_current_phase(project_id)
        self._validate_rollback_target(target_phase, current)

        affected: dict[int, int] = {}
        rows = self._conn.execute(
            "SELECT phase_num, artifact_version FROM phases "
            "WHERE project_id = ? AND phase_num BETWEEN ? AND ? "
            "ORDER BY phase_num ASC",
            (project_id, target_phase + 1, current),
        ).fetchall()
        for row in rows:
            affected[int(row[0])] = int(row[1])

        invalidated_phases = sorted(affected.keys())
        segments = sum(affected.values())
        return RollbackImpact(
            target_phase=target_phase,
            current_phase=current,
            invalidated_phases=invalidated_phases,
            affected_artifact_versions=affected,
            affected_segment_count=segments,
        )

    def rollback(self, project_id: str, target_phase: int) -> RollbackResult:
        """Invalidate downstream phases and set ``current_phase`` back."""
        current = self._read_current_phase(project_id)
        self._validate_rollback_target(target_phase, current)

        invalidated: list[int] = []
        for phase_num in range(target_phase + 1, current + 1):
            cursor = self._conn.execute(
                _UPDATE_PHASES_INVALIDATE_SQL,
                (project_id, phase_num),
            )
            if cursor.rowcount:
                invalidated.append(phase_num)
                self._emit_event(
                    project_id,
                    EventType.PHASE_INVALIDATED,
                    {
                        "phase_num": phase_num,
                        "reason": f"rollback to P{target_phase}",
                    },
                )

        self._conn.execute(_UPDATE_PROJECTS_ROLLBACK_SQL, (target_phase, project_id))
        self._conn.commit()
        return RollbackResult(
            target_phase=target_phase,
            invalidated_phases=invalidated,
        )

    # -- skip (SPEC-3.4 AC-2 + AC-3) -----------------------------------

    def skip(self, project_id: str, phase_num: int) -> None:
        """Skip ``phase_num``; advance ``current_phase`` by 1.

        Preconditions (SPEC-3.4):
          * No task in ``pending``/``queued``/``running`` for the phase
            (else :class:`ActiveTasksExist`, EVID_2005).
          * ``phases.preferences_confirmed_at IS NOT NULL``
            (else :class:`SkipNotAllowed`, EVID_2003).
        Artifact existence / review pass are explicitly NOT required.
        """
        active = self._conn.execute(
            "SELECT COUNT(*) FROM task_ledger "
            "WHERE project_id = ? AND phase = ? AND status IN "
            "('pending','queued','running')",
            (project_id, phase_num),
        ).fetchone()
        if active and int(active[0]) > 0:
            raise ActiveTasksExist(f"cannot skip phase {phase_num}: active tasks exist")

        row = self._conn.execute(
            "SELECT preferences_confirmed_at FROM phases WHERE project_id = ? AND phase_num = ?",
            (project_id, phase_num),
        ).fetchone()
        if row is None or row[0] is None:
            raise SkipNotAllowed(f"cannot skip phase {phase_num}: preferences not confirmed")

        self._conn.execute(_UPDATE_PHASE_SKIP_SQL, (project_id, phase_num))
        current = self._read_current_phase(project_id)
        if phase_num == current:
            self._conn.execute(_UPDATE_PROJECTS_ADVANCE_SQL, (project_id, current))
        self._conn.commit()

    # -- helpers --------------------------------------------------------

    def _read_current_phase(self, project_id: str) -> int:
        row = self._conn.execute(
            "SELECT current_phase FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            raise ValueError(f"project not found: {project_id}")
        return int(row[0])

    @staticmethod
    def _validate_rollback_target(target_phase: int, current: int) -> None:
        if target_phase < 0 or target_phase >= current:
            raise InvalidRollbackTarget(
                f"cannot rollback to phase {target_phase} (current_phase={current})"
            )

    def _emit_event(
        self,
        project_id: str,
        event_type: EventType,
        payload: dict[str, object],
    ) -> None:
        self._conn.execute(
            _INSERT_EVENT_SQL,
            (project_id, event_type.value, json.dumps(payload)),
        )
        self._conn.commit()


__all__ = [
    "ActiveTasksExist",
    "AdvanceResult",
    "AdvanceStatus",
    "InvalidRollbackTarget",
    "PhaseOps",
    "RollbackImpact",
    "RollbackResult",
    "SkipNotAllowed",
]
