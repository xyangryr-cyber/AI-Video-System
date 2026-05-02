"""Tests for [SPEC-C-004] Phase Skip (AC-2, AC-3).

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.4.

Test strategy:

- AC-2 skip_no_artifact_ok: seed a phase with ``artifact_version=0`` and
  NO ``artifact_path``. Skip still succeeds provided (a) no in-progress
  tasks in that phase and (b) ``preferences_confirmed_at`` is set.

- AC-3 skip_requires_no_running_and_prefs: skip MUST reject when
    * any task for that phase is in ``pending``/``queued``/``running``
      (EVID_2005), OR
    * ``preferences_confirmed_at`` is NULL (EVID_2003).
  After a successful skip the phase row flips to ``status='skipped'``
  and ``projects.current_phase`` advances by one.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "src" / "backend"
SCHEMA_FILE = BACKEND_DIR / "db" / "schema.sql"


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _seed_project(
    conn: sqlite3.Connection,
    project_id: str,
    current_phase: int = 2,
) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description, current_phase) "
        "VALUES(?, ?, ?, ?)",
        (project_id, "t", "d", current_phase),
    )
    conn.commit()


def _seed_phase(
    conn: sqlite3.Connection,
    project_id: str,
    phase_num: int,
    *,
    status: str = "active",
    artifact_version: int = 0,
    artifact_path: str | None = None,
    preferences_confirmed_at: str | None = None,
) -> None:
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name, status, "
        "artifact_version, artifact_path, preferences_confirmed_at) "
        "VALUES(?, ?, ?, ?, ?, ?, ?)",
        (
            project_id,
            phase_num,
            f"P{phase_num}",
            status,
            artifact_version,
            artifact_path,
            preferences_confirmed_at,
        ),
    )
    conn.commit()


def _seed_task(
    conn: sqlite3.Connection,
    task_id: str,
    project_id: str,
    phase: int,
    status: str,
) -> None:
    conn.execute(
        "INSERT INTO task_ledger("
        "id, project_id, phase, type, status, params) "
        "VALUES(?, ?, ?, 'generate_artifact', ?, '{}')",
        (task_id, project_id, phase, status),
    )
    conn.commit()


def _phase_status(conn: sqlite3.Connection, project_id: str, phase_num: int) -> str:
    row = conn.execute(
        "SELECT status FROM phases WHERE project_id = ? AND phase_num = ?",
        (project_id, phase_num),
    ).fetchone()
    assert row is not None
    return str(row[0])


class TestAC2SkipNoArtifactRequired:
    """AC-2: Skip does not require artifact existence or review pass."""

    def test_skip_no_artifact_ok(self) -> None:
        from src.backend.engine.phase_ops import PhaseOps
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project(conn, "proj_c004_s1", current_phase=2)
        # No artifact: artifact_version=0, artifact_path=NULL. Prefs confirmed.
        _seed_phase(
            conn,
            "proj_c004_s1",
            phase_num=2,
            status="active",
            artifact_version=0,
            artifact_path=None,
            preferences_confirmed_at="2026-04-22T10:00:00.000Z",
        )

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        ops.skip("proj_c004_s1", phase_num=2)

        assert _phase_status(conn, "proj_c004_s1", 2) == "skipped"
        row = conn.execute(
            "SELECT current_phase FROM projects WHERE project_id = ?",
            ("proj_c004_s1",),
        ).fetchone()
        assert row is not None and int(row[0]) == 3, (
            "skip must advance current_phase by 1"
        )


class TestAC3SkipRequirements:
    """AC-3: Skip requires no in-progress tasks AND preferences confirmed."""

    def test_skip_rejects_when_running_task_exists(self) -> None:
        from src.backend.engine.phase_ops import (
            ActiveTasksExist,
            PhaseOps,
        )
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project(conn, "proj_c004_s2", current_phase=2)
        _seed_phase(
            conn,
            "proj_c004_s2",
            phase_num=2,
            preferences_confirmed_at="2026-04-22T10:00:00.000Z",
        )
        _seed_task(
            conn,
            "t_100001",
            "proj_c004_s2",
            2,
            status="running",
        )

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        try:
            ops.skip("proj_c004_s2", phase_num=2)
        except ActiveTasksExist as exc:
            assert exc.error_code == "EVID_2005"
        else:
            raise AssertionError(
                "skip must raise ActiveTasksExist when a running task exists"
            )
        assert _phase_status(conn, "proj_c004_s2", 2) == "active", (
            "phase must not transition when skip is rejected"
        )

    def test_skip_rejects_when_preferences_not_confirmed(self) -> None:
        from src.backend.engine.phase_ops import (
            PhaseOps,
            SkipNotAllowed,
        )
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project(conn, "proj_c004_s3", current_phase=2)
        # Prefs NOT confirmed.
        _seed_phase(
            conn,
            "proj_c004_s3",
            phase_num=2,
            preferences_confirmed_at=None,
        )

        engine = WorkflowEngine(conn)
        ops = PhaseOps(engine)

        try:
            ops.skip("proj_c004_s3", phase_num=2)
        except SkipNotAllowed as exc:
            assert exc.error_code == "EVID_2003"
        else:
            raise AssertionError(
                "skip must raise SkipNotAllowed when prefs are not confirmed"
            )

    def test_skip_accepts_pending_and_queued_as_active(self) -> None:
        """Pending/queued tasks also count as "in-progress" (SPEC-3.4)."""
        from src.backend.engine.phase_ops import (
            ActiveTasksExist,
            PhaseOps,
        )
        from src.backend.engine.workflow_engine import WorkflowEngine

        for status in ("pending", "queued"):
            conn = sqlite3.connect(":memory:")
            _seed_schema(conn)
            pid = f"proj_c004_s4_{status}"
            _seed_project(conn, pid, current_phase=2)
            _seed_phase(
                conn,
                pid,
                phase_num=2,
                preferences_confirmed_at="2026-04-22T10:00:00.000Z",
            )
            _seed_task(conn, "t_100001", pid, 2, status=status)

            engine = WorkflowEngine(conn)
            ops = PhaseOps(engine)

            raised = False
            try:
                ops.skip(pid, phase_num=2)
            except ActiveTasksExist:
                raised = True
            assert raised, f"skip must reject while a {status!r} task exists"
