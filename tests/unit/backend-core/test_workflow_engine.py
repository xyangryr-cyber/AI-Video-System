"""Tests for [SPEC-C-001] WorkflowEngine Single-Class Implementation.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.1.

Test strategy per AC (mapped from task card):

- AC-1 All task_ledger state changes occur exclusively through the
  engine: static scan of ``src/backend/**/*.py`` for raw writes to
  ``task_ledger`` + behavioural check that ``WorkflowEngine.create_task``
  actually lands a row.

- AC-2 EventBus is a pure function: assert ``EventBus.publish`` is a
  ``staticmethod``, ``EventBus()`` carries no instance ``__dict__`` state,
  and the source file declares no module-level subscriber registry
  (``subscribers``/``listeners``/``handlers`` list/dict/set).

- AC-3 Engine reads from ``projects`` / ``phases`` / ``task_ledger``:
  behavioural test -- seed all three and assert the engine returns the
  seeded rows from dedicated reader methods.

- AC-4 Engine writes to ``phases`` / ``task_ledger`` / ``events``:
  after one ``create_task`` call, a ``task.created`` event row exists
  AND a ``task_ledger`` row exists.

- AC-5 Class file stays under 400 lines: line count of
  ``src/backend/engine/workflow_engine.py`` < 400.
"""

from __future__ import annotations

import inspect
import re
import sqlite3
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_DIR = REPO_ROOT / "src" / "backend"
SCHEMA_FILE = BACKEND_DIR / "db" / "schema.sql"
ENGINE_DIR = BACKEND_DIR / "engine"
WORKFLOW_ENGINE_FILE = ENGINE_DIR / "workflow_engine.py"

TASK_LEDGER_WRITE_RE = re.compile(
    r"\b(INSERT\s+INTO\s+task_ledger|UPDATE\s+task_ledger\s+SET|"
    r"DELETE\s+FROM\s+task_ledger)\b",
    re.IGNORECASE,
)


def _backend_py_files() -> list[Path]:
    return [p for p in BACKEND_DIR.rglob("*.py") if "__pycache__" not in p.parts]


def _seed_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def _seed_project_and_phase(
    conn: sqlite3.Connection,
    project_id: str = "proj_c001",
    phase_num: int = 0,
) -> None:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?, ?, ?)",
        (project_id, "t", "d"),
    )
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name) VALUES(?, ?, ?)",
        (project_id, phase_num, f"P{phase_num}"),
    )
    conn.commit()


class TestAC1AllStateChangesThroughEngine:
    """AC-1: All task_ledger state changes occur exclusively through
    WorkflowEngine methods; no external code writes directly to
    task_ledger table."""

    def test_state_change_only_via_engine(self):
        """Static scan: raw task_ledger writes may live only under the
        engine package or in ``task_ledger_repository.py`` (the engine's
        delegated sink).
        """
        engine_prefix = ("src", "backend", "engine")
        repo_prefix = ("src", "backend", "db", "repositories")
        stray: list[str] = []
        for py in _backend_py_files():
            rel = py.relative_to(REPO_ROOT)
            if rel.parts[: len(engine_prefix)] == engine_prefix:
                continue
            if (
                rel.parts[: len(repo_prefix)] == repo_prefix
                and rel.name == "task_ledger_repository.py"
            ):
                continue
            text = py.read_text(encoding="utf-8")
            for lineno, line in enumerate(text.splitlines(), 1):
                if TASK_LEDGER_WRITE_RE.search(line):
                    stray.append(f"{rel}:{lineno}: {line.strip()[:120]}")
        assert not stray, (
            "Only WorkflowEngine (via task_ledger_repository) may "
            "write to task_ledger. Stray writes:\n" + "\n".join(stray)
        )

    def test_create_task_lands_a_task_ledger_row(self):
        """Behavioural complement: ``WorkflowEngine.create_task``
        actually inserts a task_ledger row. Blocks a degenerate impl
        where create_task is a no-op.
        """
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        engine = WorkflowEngine(conn)
        task_id = engine.create_task(
            project_id="proj_c001",
            phase=0,
            task_type="generate_artifact",
        )
        row = conn.execute(
            "SELECT id, project_id, phase, type, status FROM task_ledger WHERE id = ?",
            (task_id,),
        ).fetchone()
        assert row is not None, "create_task must insert a row"
        assert row[1] == "proj_c001"
        assert row[2] == 0
        assert row[3] == "generate_artifact"
        assert row[4] == "pending"


class TestAC2EventBusPureFunction:
    """AC-2: EventBus is a pure function (no instance variables storing
    subscriber state, no global registry)."""

    def test_event_bus_no_instance_state(self):
        """A fresh EventBus instance carries no ``__dict__`` entries --
        i.e. no subscriber lists or handler registries.
        """
        from src.backend.engine.event_bus import EventBus

        bus = EventBus()
        instance_vars = getattr(bus, "__dict__", {})
        assert not instance_vars, (
            f"EventBus must not carry instance state; found {instance_vars!r}"
        )

    def test_event_bus_pure_function(self):
        """``publish`` must be a ``staticmethod`` (callable without a
        bound instance) and the source file must not declare a
        module-level subscriber/listener/handler registry.
        """
        from src.backend.engine.event_bus import EventBus

        publish = EventBus.__dict__.get("publish")
        assert isinstance(publish, staticmethod), (
            "EventBus.publish must be @staticmethod to prove purity "
            "(no hidden self-state)."
        )

        src_path = Path(inspect.getfile(EventBus))
        src = src_path.read_text(encoding="utf-8")
        forbidden = re.compile(
            r"^(_?subscribers|_?listeners|_?handlers)\s*"
            r"(:\s*[^=]+)?=\s*(\[|\{|set\()",
            re.MULTILINE,
        )
        assert not forbidden.search(src), (
            "event_bus.py must not declare a module-level "
            "subscriber/listener/handler registry."
        )


class TestAC3EngineReadsProjectsPhasesLedger:
    """AC-3: WorkflowEngine reads from ``projects``, ``phases``, and
    ``task_ledger`` tables as inputs."""

    def test_engine_reads_projects_phases_ledger(self):
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        engine = WorkflowEngine(conn)
        task_id = engine.create_task(
            project_id="proj_c001",
            phase=0,
            task_type="generate_artifact",
        )

        project = engine.get_project("proj_c001")
        phase = engine.get_phase("proj_c001", 0)
        task = engine.get_task(task_id)

        assert project is not None, "engine must read projects"
        assert project["project_id"] == "proj_c001"

        assert phase is not None, "engine must read phases"
        assert phase["phase_num"] == 0

        assert task is not None, "engine must read task_ledger"
        assert task["id"] == task_id
        assert task["type"] == "generate_artifact"


class TestAC4EngineWritesCorrectTables:
    """AC-4: WorkflowEngine writes to ``phases`` (status/artifact_
    version), ``task_ledger`` (new tasks/status changes), and
    ``events`` table."""

    def test_engine_writes_events_on_mutation(self):
        from src.backend.engine.workflow_engine import WorkflowEngine

        conn = sqlite3.connect(":memory:")
        _seed_schema(conn)
        _seed_project_and_phase(conn)

        engine = WorkflowEngine(conn)

        before = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        assert before == 0

        task_id = engine.create_task(
            project_id="proj_c001",
            phase=0,
            task_type="generate_artifact",
        )

        rows = conn.execute(
            "SELECT type FROM events WHERE project_id = ?",
            ("proj_c001",),
        ).fetchall()
        types = [r[0] for r in rows]
        assert "task.created" in types, (
            f"create_task must emit a task.created event; got {types}"
        )

        task_row = conn.execute(
            "SELECT id FROM task_ledger WHERE id = ?", (task_id,)
        ).fetchone()
        assert task_row is not None, "create_task must also land a task_ledger row"


class TestAC5ClassFileUnder400Lines:
    """AC-5: Class file stays under 400 lines (HARNESS §6)."""

    def test_engine_file_line_count_under_400(self):
        assert WORKFLOW_ENGINE_FILE.exists(), (
            f"workflow_engine.py missing at {WORKFLOW_ENGINE_FILE}"
        )
        line_count = len(WORKFLOW_ENGINE_FILE.read_text(encoding="utf-8").splitlines())
        assert line_count < 400, (
            f"workflow_engine.py is {line_count} lines; HARNESS §6 limit is 400."
        )
