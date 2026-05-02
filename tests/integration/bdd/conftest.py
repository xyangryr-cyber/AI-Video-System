"""pytest-bdd shared fixtures for integration scenarios.

Fixtures declared here are visible to every step module under steps/.
Keep this file thin: only cross-cutting setup (temp dirs, DB handles,
SUT factories). Tag-specific fixtures live in steps/<tag>_steps.py.

SPEC-G-000e: 4 BDD fixtures added:
  - bdd_db_conn: :memory: SQLite with all migrations run (10 tables)
  - bdd_huey: build_huey(immediate=True) for synchronous dispatch
  - bdd_dispatcher: Dispatcher wired with bdd_huey + TASK_REGISTRY
  - bdd_workflow_engine: WorkflowEngine backed by bdd_db_conn
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

_PROJECT_ROOT = Path(__file__).parents[3]
_MIGRATIONS_CORE = _PROJECT_ROOT / "src" / "backend" / "db" / "migrations"
_MIGRATIONS_EXT = _PROJECT_ROOT / "migrations"


@pytest.fixture
def scenario_state():
    """Mutable dict passed between Given/When/Then of one scenario.

    pytest-bdd recreates fixtures per scenario — resetting state is automatic.
    Use: steps read and write keys here instead of passing state via closures.
    """
    return {}


@pytest.fixture
def sut_router():
    """Lazy-import IntentRouter so tests fail early if impl is missing."""
    from src.backend.agents.intent_router import IntentRouter

    return IntentRouter()


# ---- SPEC-G-000e BDD infrastructure fixtures ----------------------------


@pytest.fixture
def bdd_db_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    for path in sorted(_MIGRATIONS_CORE.glob("*.sql")):
        conn.executescript(path.read_text())
    for path in sorted(_MIGRATIONS_EXT.glob("V*.sql")):
        conn.executescript(path.read_text())

    # Rebuild order matters: rebuild task_ledger FIRST, then async_tasks.
    #
    # SQLite (>= 3.26) auto-updates FK references during ALTER TABLE RENAME.
    # V005 renames task_ledger -> task_ledger__v315 and drops it, leaving
    # async_tasks.ledger_task_id with a dangling FK to task_ledger__v315.
    # Rebuilding task_ledger here uses the same RENAME/DROP dance, so we
    # must follow it with an async_tasks rebuild that recreates a fresh
    # FK reference to the new live task_ledger.

    # 1) Extend task_ledger.type CHECK to include SPEC-G phase-level task
    # types (generate_narration, preview_mix, plan_layout,
    # render_keyframes, compose_rough_cut, export_final). V005 only
    # covers the v3.16 BDD enum; the 6 SPEC-G types were added by
    # SPEC-G-000-pre to the Python TaskType enum but have no migration yet.
    conn.execute("PRAGMA foreign_keys = OFF")
    conn.executescript("""
        ALTER TABLE task_ledger RENAME TO task_ledger__v315;
        CREATE TABLE task_ledger (
            id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(project_id),
            phase INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN (
                'generate_artifact','regenerate_section','regenerate_shot',
                'user_revision','review','research','verify','cross_check',
                'user_annotation',
                'challenge_claim','supplement_claim','request_chart',
                'view_phase_detail','save_stage_preference','insert_section',
                'generate_narration','preview_mix','plan_layout',
                'render_keyframes','compose_rough_cut','export_final'
            )),
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN (
                'pending','queued','running','succeeded','failed','superseded','timeout'
            )),
            depends_on TEXT,
            produces_version INTEGER,
            target_version INTEGER,
            params TEXT NOT NULL DEFAULT '{}',
            result_ref TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
            updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        INSERT INTO task_ledger SELECT * FROM task_ledger__v315;
        DROP TABLE task_ledger__v315;
    """)

    # 2) Rebuild async_tasks so its FK points to the new live task_ledger.
    # Must come after the task_ledger rebuild — otherwise the rebuild's
    # auto-rename leaves async_tasks.ledger_task_id dangling again.
    conn.executescript("""
        CREATE TABLE async_tasks_fixed (
            task_id TEXT PRIMARY KEY,
            project_id TEXT NOT NULL REFERENCES projects(project_id),
            phase INTEGER NOT NULL,
            ledger_task_id TEXT REFERENCES task_ledger(id),
            type TEXT NOT NULL,
            params TEXT NOT NULL DEFAULT '{}',
            status TEXT NOT NULL DEFAULT 'pending'
                CHECK(status IN ('pending','queued','running','succeeded','failed','cancelled')),
            progress INTEGER NOT NULL DEFAULT 0 CHECK(progress BETWEEN 0 AND 100),
            worker_id TEXT,
            attempt INTEGER NOT NULL DEFAULT 1,
            max_attempts INTEGER NOT NULL DEFAULT 3,
            started_at TEXT,
            finished_at TEXT,
            error TEXT,
            created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
        );
        INSERT INTO async_tasks_fixed SELECT * FROM async_tasks;
        DROP TABLE async_tasks;
        ALTER TABLE async_tasks_fixed RENAME TO async_tasks;
    """)
    conn.execute("PRAGMA foreign_keys = ON")

    return conn


@pytest.fixture
def bdd_huey():
    from src.backend.workers.huey_config import build_huey

    return build_huey(immediate=True)


@pytest.fixture
def bdd_workflow_engine(bdd_db_conn):
    from src.backend.engine.workflow_engine import WorkflowEngine

    return WorkflowEngine(conn=bdd_db_conn)


@pytest.fixture
def bdd_dispatcher(bdd_workflow_engine, bdd_huey):
    from src.backend.engine.dispatcher import Dispatcher
    from src.backend.workers.huey_config import huey_enqueue_runner
    from src.backend.workers.tasks import TASK_REGISTRY

    return Dispatcher(
        engine=bdd_workflow_engine,
        task_runner=huey_enqueue_runner(bdd_huey, TASK_REGISTRY),
    )
