"""Tests for [SPEC-C-004] Phase Advance Idempotency (AC-5, AC-6, AC-7).

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.7.

Test strategy:

- AC-5 advance_idempotent_duplicate: two sequential ``advance`` calls.
  First call passes gate and advances. Second call (gate fn recorded
  but must NOT be invoked again) returns ``already_advanced`` with the
  current (post-advance) phase. The gate_check_fn call counter stays
  at 1.

- AC-6 advance_optimistic_lock_conflict: simulate a concurrent writer
  bumping ``projects.current_phase`` between our read and UPDATE (by
  mutating the DB inside the gate callback). Advance returns
  ``already_advanced`` + current phase rather than raising.

- AC-7 advance_concurrent_gate_409: while one thread is inside the
  gate check, a second advance call on the same project returns
  ``gate_in_progress`` + ``error_code='EVID_2002'`` without running
  the gate a second time.
"""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "src" / "backend"
SCHEMA_FILE = BACKEND_DIR / "db" / "schema.sql"


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _seed_project(
    conn: sqlite3.Connection,
    project_id: str,
    current_phase: int,
) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description, current_phase) "
        "VALUES(?, ?, ?, ?)",
        (project_id, "t", "d", current_phase),
    )
    conn.commit()


def _current_phase(conn: sqlite3.Connection, project_id: str) -> int:
    row = conn.execute(
        "SELECT current_phase FROM projects WHERE project_id = ?",
        (project_id,),
    ).fetchone()
    assert row is not None
    return int(row[0])


def _make_pass_gate():
    """Return (fn, counter-list). fn records its calls then returns True."""
    calls: list[tuple[str, int]] = []

    def _fn(project_id: str, from_phase: int) -> bool:
        calls.append((project_id, from_phase))
        return True

    return _fn, calls


class TestAC5AdvanceIdempotentDuplicate:
    """AC-5: duplicate POST advance does NOT re-execute the gate check."""

    def test_advance_idempotent_duplicate(self) -> None:
        from src.backend.engine.phase_ops import PhaseOps
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project(conn, "proj_c004_a5", current_phase=3)

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        gate_fn, calls = _make_pass_gate()

        r1 = ops.advance("proj_c004_a5", gate_check_fn=gate_fn)
        assert r1.status == "advanced"
        assert r1.current_phase == 4
        assert r1.from_phase == 3
        assert len(calls) == 1

        # Second call: current_phase is now 4, no gate run expected.
        r2 = ops.advance("proj_c004_a5", gate_check_fn=gate_fn)
        assert r2.status == "already_advanced", (
            f"expected already_advanced on duplicate advance, got {r2.status}"
        )
        assert r2.current_phase == 4
        # Gate must NOT have been invoked a second time; the engine
        # short-circuits on "nothing to advance from this snapshot".
        assert len(calls) == 1, "duplicate advance must not re-invoke gate_check_fn"


class TestAC6OptimisticLockConflict:
    """AC-6: affected_rows=0 UPDATE returns current state, not an error."""

    def test_advance_optimistic_lock_conflict(self) -> None:
        from src.backend.engine.phase_ops import PhaseOps
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project(conn, "proj_c004_a6", current_phase=3)

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        # Inside the gate callback, simulate a concurrent writer moving
        # projects.current_phase from 3 to 4 -- our subsequent optimistic
        # UPDATE WHERE current_phase = 3 will affect 0 rows.
        def racing_gate(project_id: str, from_phase: int) -> bool:
            conn.execute(
                "UPDATE projects SET current_phase = ? WHERE project_id = ?",
                (4, project_id),
            )
            conn.commit()
            return True

        result = ops.advance("proj_c004_a6", gate_check_fn=racing_gate)

        assert result.status == "already_advanced", (
            f"optimistic-lock loss must return already_advanced, got {result.status}"
        )
        assert result.current_phase == 4, (
            "result must reflect the post-race current_phase"
        )
        # Phase did not double-increment.
        assert _current_phase(conn, "proj_c004_a6") == 4


class TestAC7ConcurrentGateReturns409:
    """AC-7: second advance while first is inside gate returns EVID_2002."""

    def test_advance_concurrent_gate_409(self) -> None:
        from src.backend.engine.phase_ops import PhaseOps
        from src.backend.engine.workflow_engine import WorkflowEngine

        # check_same_thread=False: SPEC-3.7 AC-7 requires exercising the
        # single-flight lock from a second thread; the in-memory SQLite
        # connection is otherwise thread-pinned.
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        _seed_schema(conn)
        _seed_project(conn, "proj_c004_a7", current_phase=3)

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        gate_entered = threading.Event()
        gate_release = threading.Event()
        inner_calls: list[int] = []

        def blocking_gate(project_id: str, from_phase: int) -> bool:
            inner_calls.append(from_phase)
            gate_entered.set()
            gate_release.wait(timeout=3.0)
            return True

        first_result: list = []

        def run_first() -> None:
            first_result.append(
                ops.advance("proj_c004_a7", gate_check_fn=blocking_gate)
            )

        t = threading.Thread(target=run_first)
        t.start()

        # Wait until the first call is parked inside the gate.
        assert gate_entered.wait(timeout=3.0), "first gate never entered"

        # Second call while the lock is held: must return 409/EVID_2002
        # without invoking the gate again.
        second_calls: list[int] = []

        def second_gate(project_id: str, from_phase: int) -> bool:
            second_calls.append(from_phase)
            return True

        r2 = ops.advance("proj_c004_a7", gate_check_fn=second_gate)

        assert r2.status == "gate_in_progress"
        assert r2.error_code == "EVID_2002"
        assert r2.current_phase == 3, (
            "concurrent rejection reflects pre-advance phase snapshot"
        )
        assert second_calls == [], (
            "concurrent advance must NOT invoke its gate callback"
        )

        # Release the first call; it should complete with advanced.
        gate_release.set()
        t.join(timeout=3.0)
        assert not t.is_alive(), "first advance thread did not finish"
        assert first_result and first_result[0].status == "advanced"
        assert first_result[0].current_phase == 4
        assert inner_calls == [3], "first gate ran exactly once"
