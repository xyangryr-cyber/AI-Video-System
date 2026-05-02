"""[SPEC-B-015] Integration tests: AC-4 (retry -> missing) + AC-5 (async_tasks
one-to-one with Huey invocations).

AC-5 note on "task_ledger": the task card wording "对应 task_ledger 记录" is
reconciled against the DDL — `task_ledger.type` CHECK constraint (V005, 15-value
v3.16 enum) does NOT include material_fetch / material_verify. The matching
table is `async_tasks` (schema.sql:60), whose `type` column is free-form and
whose row is what Huey wrappers create per invocation. The one-to-one test
therefore targets `async_tasks`. See commit body Decisions for the full
reconciliation.
"""

from __future__ import annotations

import json
import sqlite3

import pytest


SCHEMA_MIN = """
CREATE TABLE projects (
    project_id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE task_ledger (
    id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    phase INTEGER NOT NULL,
    type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    params TEXT NOT NULL DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
    updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE TABLE async_tasks (
    task_id TEXT PRIMARY KEY,
    project_id TEXT NOT NULL REFERENCES projects(project_id),
    phase INTEGER NOT NULL,
    ledger_task_id TEXT REFERENCES task_ledger(id),
    type TEXT NOT NULL,
    params TEXT NOT NULL DEFAULT '{}',
    status TEXT NOT NULL DEFAULT 'pending',
    progress INTEGER NOT NULL DEFAULT 0,
    worker_id TEXT,
    attempt INTEGER NOT NULL DEFAULT 1,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    started_at TEXT,
    finished_at TEXT,
    error TEXT,
    created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
"""


@pytest.fixture()
def db():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA_MIN)
    conn.execute(
        "INSERT INTO projects(project_id, user_id) VALUES (?, ?)",
        ("proj_001", "user_default"),
    )
    conn.commit()
    yield conn
    conn.close()


# --- AC-4 ---------------------------------------------------------------


class _TransientProvider:
    """Always raises 5xx on fetch."""

    def __init__(self, error_code=503):
        self.error_code = error_code
        self.calls = 0

    def fetch(self, material_id):
        self.calls += 1
        from src.backend.workers.p7a_tasks import TransientProviderError

        raise TransientProviderError(
            f"HTTP {self.error_code}", status_code=self.error_code
        )


class TestAC4FetchRetryToMissing:
    """On 5xx fetch failure, retry to cap (3), then write
    verification_status=missing to the manifest."""

    def test_exhausted_retries_mark_material_missing(self, tmp_path):
        from src.backend.workers.p7a_tasks import (
            fetch_with_retry,
            FetchExhaustedError,
        )

        manifest_path = tmp_path / "material_manifest.json"
        manifest_path.write_text(
            json.dumps(
                {
                    "shots": {"shot_001": {"material_id": "m_1"}},
                    "materials": {
                        "m_1": {
                            "material_id": "m_1",
                            "verification_status": "pending",
                        }
                    },
                }
            )
        )

        provider = _TransientProvider(error_code=503)
        with pytest.raises(FetchExhaustedError):
            fetch_with_retry(
                provider=provider,
                manifest_path=manifest_path,
                material_id="m_1",
                max_attempts=3,
            )

        # Provider called exactly 3 times (initial + 2 retries)
        assert provider.calls == 3
        # Manifest updated in place
        new_manifest = json.loads(manifest_path.read_text())
        assert new_manifest["materials"]["m_1"]["verification_status"] == "missing"

    def test_non_transient_error_does_not_retry(self, tmp_path):
        """4xx errors are permanent; no retry, manifest untouched."""
        from src.backend.workers.p7a_tasks import fetch_with_retry

        class _Perma:
            calls = 0

            def fetch(self, mid):
                self.calls += 1
                raise ValueError("bad material id")

        manifest_path = tmp_path / "m.json"
        manifest_path.write_text(
            json.dumps({"materials": {"m_1": {"verification_status": "pending"}}})
        )
        provider = _Perma()
        with pytest.raises(ValueError):
            fetch_with_retry(
                provider=provider,
                manifest_path=manifest_path,
                material_id="m_1",
                max_attempts=3,
            )
        # Only one call (not retried)
        assert provider.calls == 1
        data = json.loads(manifest_path.read_text())
        # Manifest not touched by a permanent error path
        assert data["materials"]["m_1"]["verification_status"] == "pending"


# --- AC-5 ---------------------------------------------------------------


class TestAC5HueyToAsyncTasksOneToOne:
    """record_huey_task writes exactly one async_tasks row per invocation,
    typed material_fetch / material_verify / chart_material_fetch."""

    def test_material_fetch_creates_async_task_row(self, db):
        from src.backend.workers.p7a_tasks import record_huey_task

        record_huey_task(
            db,
            task_id="huey_task_001",
            project_id="proj_001",
            phase=7,
            task_type="material_fetch",
            params={"material_id": "m_1"},
        )
        rows = db.execute(
            "SELECT task_id, type, project_id, phase, params, max_attempts "
            "FROM async_tasks"
        ).fetchall()
        assert len(rows) == 1
        r = rows[0]
        assert r["task_id"] == "huey_task_001"
        assert r["type"] == "material_fetch"
        assert r["project_id"] == "proj_001"
        assert r["phase"] == 7
        assert json.loads(r["params"]) == {"material_id": "m_1"}
        assert r["max_attempts"] == 3

    def test_material_verify_creates_async_task_row(self, db):
        from src.backend.workers.p7a_tasks import record_huey_task

        record_huey_task(
            db,
            task_id="huey_task_002",
            project_id="proj_001",
            phase=7,
            task_type="material_verify",
            params={"material_id": "m_1"},
        )
        r = db.execute(
            "SELECT type, max_attempts FROM async_tasks WHERE task_id = 'huey_task_002'"
        ).fetchone()
        assert r["type"] == "material_verify"
        # material_verify retries=2 -> max_attempts=2
        assert r["max_attempts"] == 2

    def test_one_invocation_writes_exactly_one_row(self, db):
        """AC-5: one-to-one between Huey invocation and async_tasks row."""
        from src.backend.workers.p7a_tasks import record_huey_task

        for i in range(5):
            record_huey_task(
                db,
                task_id=f"huey_task_{i:03d}",
                project_id="proj_001",
                phase=7,
                task_type="material_fetch",
                params={"material_id": f"m_{i}"},
            )
        count = db.execute("SELECT COUNT(*) AS c FROM async_tasks").fetchone()["c"]
        assert count == 5

    def test_rejected_task_type_raises(self, db):
        """Only the three P7A task types may be recorded through this wrapper."""
        from src.backend.workers.p7a_tasks import record_huey_task

        with pytest.raises(ValueError):
            record_huey_task(
                db,
                task_id="x",
                project_id="proj_001",
                phase=7,
                task_type="generate_artifact",  # not a P7A task
                params={},
            )
