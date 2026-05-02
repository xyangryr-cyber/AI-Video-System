"""[SPEC-C-012] Producer Programmatic Steps & Async Review Execution."""

import hashlib
import json
import sqlite3

import pytest

from src.backend.agents.producer_steps import (
    compute_bgm_envelope,
    compute_roughcut_params,
    compute_sfx_timeline,
    compute_ssml,
    compute_word_count,
)
from src.backend.engine.workflow_engine import WorkflowEngine


# ---------------------------------------------------------------------------
# AC-1: deterministic across 10 runs
# ---------------------------------------------------------------------------


class TestAC1DeterministicOutput10Runs:
    def _hash_output(self, func, *args, **kwargs):
        result = func(*args, **kwargs)
        serialized = json.dumps(result, sort_keys=True, ensure_ascii=False, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def test_deterministic_output_10_runs(self):
        segments = [
            {"segment_id": "seg_1", "start_sec": 0.0, "end_sec": 10.0},
            {"segment_id": "seg_2", "start_sec": 10.0, "end_sec": 20.0},
        ]
        steps = [
            (compute_ssml, ("测试文本",), {"rate": 1.0, "emotion": "neutral"}),
            (compute_bgm_envelope, (segments,), {"total_duration_sec": 20.0}),
            (compute_sfx_timeline, (segments,), {}),
            (compute_roughcut_params, (segments,), {"fps": 30}),
            (compute_word_count, ("hello world test",), {}),
        ]
        for func, args, kwargs in steps:
            hashes = {self._hash_output(func, *args, **kwargs) for _ in range(10)}
            assert len(hashes) == 1, f"{func.__name__} produced different outputs"


# ---------------------------------------------------------------------------
# AC-2: zero LLM calls
# ---------------------------------------------------------------------------


class TestAC2NoLlmCalls:
    def test_no_llm_calls(self):
        with open("src/backend/agents/producer_steps.py") as f:
            source = f.read()
        for banned in (
            "litellm",
            "openai",
            "anthropic",
            "llm_service",
            "chat_completion",
        ):
            assert banned not in source.lower(), (
                f"producer_steps.py references {banned}"
            )


# ---------------------------------------------------------------------------
# AC-3: artifact immediately readable while review pending
# ---------------------------------------------------------------------------


@pytest.fixture
def engine_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute("""CREATE TABLE IF NOT EXISTS projects (
        project_id TEXT PRIMARY KEY, title TEXT, current_phase INTEGER, status TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS task_ledger (
        id TEXT PRIMARY KEY, project_id TEXT, phase INTEGER, type TEXT,
        status TEXT, params TEXT, produces_version TEXT, target_version TEXT,
        result_ref TEXT, created_at TEXT, updated_at TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT, type TEXT, payload TEXT)""")
    conn.execute("""CREATE TABLE IF NOT EXISTS phases (
        project_id TEXT, phase INTEGER, status TEXT,
        artifact_path TEXT, PRIMARY KEY (project_id, phase))""")
    conn.execute(
        "INSERT INTO projects(project_id, title, current_phase, status) VALUES('proj_1','test',1,'active')"
    )
    conn.execute(
        "INSERT INTO phases(project_id, phase, status) VALUES('proj_1',1,'in_progress')"
    )
    conn.commit()
    yield conn
    conn.close()


class TestAC3ArtifactReadableDuringReview:
    def test_artifact_readable_during_review(self, engine_conn):
        engine = WorkflowEngine(engine_conn)
        # Producer writes artifact
        engine_conn.execute(
            "UPDATE phases SET artifact_path = ? WHERE project_id = ? AND phase = ?",
            ("/artifacts/script_v1.json", "proj_1", 1),
        )
        engine_conn.commit()
        # Create review as pending
        engine.create_task(
            project_id="proj_1",
            phase=1,
            task_type="review",
            params={
                "phase_name": "script",
                "reviewer_name": "l1",
                "artifact_path": "/artifacts/script_v1.json",
            },
            target_version=1,
        )
        # Artifact is readable
        row = engine_conn.execute(
            "SELECT artifact_path FROM phases WHERE project_id = ? AND phase = ?",
            ("proj_1", 1),
        ).fetchone()
        assert row["artifact_path"] == "/artifacts/script_v1.json"
        # Review exists as pending
        task = engine_conn.execute(
            "SELECT status FROM task_ledger WHERE project_id = ? AND type = 'review'",
            ("proj_1",),
        ).fetchone()
        assert task["status"] == "pending"


# ---------------------------------------------------------------------------
# AC-4: review completion emits ws event
# ---------------------------------------------------------------------------


class TestAC4ReviewCompleteEmitsWsEvent:
    def test_review_complete_emits_ws_event(self, engine_conn):
        engine = WorkflowEngine(engine_conn)
        engine.create_task(
            project_id="proj_1",
            phase=1,
            task_type="review",
            params={
                "phase_name": "script",
                "reviewer_name": "l1",
                "artifact_path": "/artifacts/script_v1.json",
            },
            target_version=1,
        )
        task = engine_conn.execute(
            "SELECT id FROM task_ledger WHERE project_id = ? AND type = 'review'",
            ("proj_1",),
        ).fetchone()
        engine.complete_task(task["id"])
        events = engine_conn.execute(
            "SELECT * FROM events WHERE project_id = ? AND type = ?",
            ("proj_1", "review.completed"),
        ).fetchall()
        assert len(events) >= 1


# ---------------------------------------------------------------------------
# AC-5: review_status computed from task_ledger
# ---------------------------------------------------------------------------


class TestAC5ReviewStatusComputedNotStored:
    def test_review_status_computed_not_stored(self, engine_conn):
        engine = WorkflowEngine(engine_conn)
        engine.create_task(
            project_id="proj_1",
            phase=1,
            task_type="review",
            params={
                "phase_name": "script",
                "reviewer_name": "l1",
                "artifact_path": "/artifacts/script_v1.json",
            },
            target_version=1,
        )
        # Compute from task_ledger
        status = engine.compute_review_status("proj_1", 1)
        assert status in ("pending", "clean", "in_progress")
        # Complete all reviews
        engine_conn.execute(
            "UPDATE task_ledger SET status = 'succeeded' WHERE project_id = ? AND type = 'review'",
            ("proj_1",),
        )
        engine_conn.commit()
        status2 = engine.compute_review_status("proj_1", 1)
        assert status2 in ("succeeded", "clean")
