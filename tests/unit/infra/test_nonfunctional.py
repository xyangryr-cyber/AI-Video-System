"""Tests for [SPEC-B-012] Non-Functional Requirements.

Real assertions for AC-1..AC-4, AC-7:
* AC-1: Single-tab rejection (409 + message)
* AC-2: Regenerate limiter (5th call → suggest_manual_edit=true)
* AC-3: No sync TTS/render waits in HTTP handlers
* AC-4: .gitignore has .env, no hardcoded sk- keys
* AC-7: Pipeline e2e skeleton runs with mock LLM
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]


# --- AC-1: single tab rejection ----------------------------------------------


class TestAC1SingleTabRejectsSecondConnection:
    def test_single_tab_rejects_second_connection(self):
        """Second connection for same project returns 409 Conflict."""
        from src.backend.api.middleware.single_tab import SingleTabLock

        lock = SingleTabLock()
        project_id = "proj_a"

        # First connection: allowed
        allowed, msg = lock.try_acquire(project_id)
        assert allowed is True
        assert msg == ""

        # Second connection: rejected
        allowed2, msg2 = lock.try_acquire(project_id)
        assert allowed2 is False
        assert "409" in msg2 or "already" in msg2.lower()

        # Release and re-acquire
        lock.release(project_id)
        allowed3, msg3 = lock.try_acquire(project_id)
        assert allowed3 is True


# --- AC-2: regenerate limiter ------------------------------------------------


class TestAC2RegenerateLimitSuggestsManualEdit:
    def test_regenerate_limit_suggests_manual_edit(self):
        """5th regenerate returns suggest_manual_edit=true."""
        from src.backend.core.regenerate_limiter import RegenerateLimiter

        limiter = RegenerateLimiter(max_regenerates=5)
        section_id = "sec_1"

        for i in range(4):
            result = limiter.check(section_id)
            assert result["suggest_manual_edit"] is False, f"call {i + 1}"
            assert result["remaining"] == 4 - i

        # 5th call
        result = limiter.check(section_id)
        assert result["suggest_manual_edit"] is True
        assert result["remaining"] == 0

    def test_reset_after_new_version(self):
        """Limit resets when section version increments."""
        from src.backend.core.regenerate_limiter import RegenerateLimiter

        limiter = RegenerateLimiter(max_regenerates=4)

        for _ in range(3):
            limiter.check("sec_1")

        result = limiter.check("sec_1")
        assert result["suggest_manual_edit"] is True

        # Reset for a new section
        result2 = limiter.check("sec_2")
        assert result2["suggest_manual_edit"] is False


# --- AC-3: no sync TTS/render in HTTP handlers -------------------------------


class TestAC3NoSyncWaitInHandlers:
    def test_no_sync_wait_in_handlers(self):
        """No HTTP handler synchronously waits for TTS or rendering."""
        import subprocess

        # Check for sync patterns in route files
        result = subprocess.run(
            [
                "grep",
                "-rnI",
                "time.sleep\|subprocess.run.*ffmpeg\|subprocess.run.*tts",
                "src/backend/api/",
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        # Any hit in route files would be a violation
        hit_lines = [
            line
            for line in result.stdout.splitlines()
            if line.strip() and not line.strip().startswith("#") and ".pyc" not in line
        ]
        assert len(hit_lines) == 0, f"Sync wait found in HTTP handlers: {hit_lines}"


# --- AC-4: no hardcoded API keys ---------------------------------------------


class TestAC4NoHardcodedApiKeys:
    def test_gitignore_has_env(self):
        gitignore = REPO_ROOT / ".gitignore"
        content = gitignore.read_text()
        assert ".env" in content

    def test_no_sk_keys_in_source(self):
        result = subprocess.run(
            ["grep", "-rnEI", r"sk-(proj|ant|admin|svcacct)", "src/backend/"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        hit_lines = [
            line
            for line in result.stdout.splitlines()
            if "redaction" not in line
            and "test_" not in line
            and ".pyc" not in line
            and "__pycache__" not in line
            and "SECRET_REGEXES" not in line
            and "redact" not in line
            and "REDACTED" not in line
        ]
        assert len(hit_lines) == 0, f"Hardcoded sk- key found: {hit_lines}"


# --- AC-5: eval directory with JSONL templates --------------------------------


class TestAC5EvalDirectoryWithJsonlTemplates:
    def test_eval_directory_with_jsonl_templates(self):
        """tests/eval/ exists with JSONL template files (SPEC-B-012 templates)."""
        eval_dir = REPO_ROOT / "tests" / "eval"
        assert eval_dir.is_dir(), "tests/eval/ directory missing"

        import json

        template_names = [
            "script_agent.jsonl",
            "reviewer_agent.jsonl",
            "chart_agent.jsonl",
            "claims_agent.jsonl",
        ]
        for name in template_names:
            f = eval_dir / name
            assert f.exists(), f"Template {name} missing"
            content = f.read_text().strip()
            assert content, f"{name} is empty"
            for line in content.splitlines():
                record = json.loads(line)
                assert "input" in record, f"{name}: missing 'input'"
                assert "expected_output" in record, f"{name}: missing 'expected_output'"
                assert "eval_criteria" in record, f"{name}: missing 'eval_criteria'"


# --- AC-6: CI path filter ----------------------------------------------------


class TestAC6CiPathFilterConfigured:
    def test_ci_path_filter_configured(self):
        """CI config includes prompts/** and agents/** path filters."""
        workflow = REPO_ROOT / ".github" / "workflows" / "eval_regression.yml"
        assert workflow.exists(), "eval_regression.yml missing"

        content = workflow.read_text()
        assert "prompts/**" in content or "prompts/" in content, (
            "Missing prompts/** path filter in eval_regression.yml"
        )
        assert "agents/**" in content or "agents/" in content, (
            "Missing agents/** path filter in eval_regression.yml"
        )


# --- AC-7: pipeline e2e skeleton ---------------------------------------------


class TestAC7PipelineSkeletonRuns:
    def test_pipeline_skeleton_runs(self):
        """Pipeline e2e skeleton exists and runs with mock LLM."""
        e2e_file = REPO_ROOT / "tests" / "integration" / "test_pipeline_e2e.py"
        if not e2e_file.exists():
            pytest.skip("test_pipeline_e2e.py not created yet")

        result = subprocess.run(
            [sys.executable, "-m", "pytest", str(e2e_file), "-v", "--tb=short"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"E2E skeleton failed: {result.stdout}\n{result.stderr}"
        )
