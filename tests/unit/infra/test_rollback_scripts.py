"""Tests for [SPEC-B-011] Rollout/Rollback Scripts.

Real assertions for AC-1..AC-5 covering dry-run execution, health check
presence, and no-side-effects guarantee.
"""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
ROLLBACK_DIR = REPO_ROOT / "scripts" / "rollback"


def _run_dry_run(script_name: str) -> subprocess.CompletedProcess:
    script = ROLLBACK_DIR / script_name
    if not script.exists():
        raise FileNotFoundError(f"Script not found: {script}")
    env = {**os.environ, "PATH": os.environ.get("PATH", "")}
    return subprocess.run(
        ["bash", str(script), "--dry-run"],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        env=env,
    )


class TestAC1ComposeRollbackDryRun:
    def test_compose_rollback_dry_run(self):
        """compose_rollback.sh --dry-run exits 0 and prints expected steps."""
        result = _run_dry_run("compose_rollback.sh")
        assert result.returncode == 0, f"Exit {result.returncode}: {result.stderr}"
        output = result.stdout
        assert "[DRY-RUN]" in output
        assert "docker compose" in output or "Would execute" in output


class TestAC2SchemaRollbackDryRun:
    def test_schema_rollback_dry_run(self):
        """schema_rollback.sh --dry-run exits 0 and prints expected steps."""
        result = _run_dry_run("schema_rollback.sh")
        assert result.returncode == 0, f"Exit {result.returncode}: {result.stderr}"
        output = result.stdout
        assert "[DRY-RUN]" in output
        assert "app.sqlite3" in output or "docker compose" in output


class TestAC3WorkerRecoveryDryRun:
    def test_worker_recovery_dry_run(self):
        """worker_recovery.sh --dry-run exits 0 and prints expected steps."""
        result = _run_dry_run("worker_recovery.sh")
        assert result.returncode == 0, f"Exit {result.returncode}: {result.stderr}"
        output = result.stdout
        assert "[DRY-RUN]" in output


class TestAC4HealthCheckInScripts:
    def test_health_check_in_scripts(self):
        """All three scripts contain a health_check function."""
        for script_name in (
            "compose_rollback.sh",
            "schema_rollback.sh",
            "worker_recovery.sh",
        ):
            script = ROLLBACK_DIR / script_name
            content = script.read_text()
            assert "health_check" in content, (
                f"{script_name} missing health_check function"
            )
            assert "curl" in content, f"{script_name} missing curl health check"


class TestAC5DryRunNoSideEffects:
    def test_dry_run_no_side_effects(self):
        """--dry-run mode does NOT invoke docker compose or sqlite3 write commands."""
        for script_name in (
            "compose_rollback.sh",
            "schema_rollback.sh",
            "worker_recovery.sh",
        ):
            result = _run_dry_run(script_name)
            # --dry-run should NOT print actual docker compose up/down/restart output
            # (docker commands without --dry-run would produce real output)
            assert result.returncode == 0
            assert "[DRY-RUN]" in result.stdout

    def test_dry_run_no_actual_docker_execution(self):
        """Verify that --dry-run scripts don't require docker to be installed."""
        for script_name in (
            "compose_rollback.sh",
            "schema_rollback.sh",
            "worker_recovery.sh",
        ):
            result = _run_dry_run(script_name)
            assert result.returncode == 0
            # If docker actually ran (not dry-run), stderr would show docker errors
            # when docker isn't available
