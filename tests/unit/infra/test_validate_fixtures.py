"""SPEC-B-017 AC-3: fixtures must validate against emitted JSON Schemas."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[3]
SCRIPT = REPO / "scripts" / "validate_fixtures.py"
FIXTURES_DIR = REPO / "tests" / "fixtures" / "api"


def _run_validator() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=REPO,
        capture_output=True,
        text=True,
    )


def test_valid_fixtures_pass():
    result = _run_validator()
    assert result.returncode == 0, (
        f"validator failed:\nstdout={result.stdout}\nstderr={result.stderr}"
    )


def test_invalid_fixture_fails(tmp_path, monkeypatch):
    bogus = FIXTURES_DIR / "projects" / "_bogus_invalid.json"
    bogus.write_text(json.dumps({"definitely": "not a valid project"}))
    try:
        result = _run_validator()
        assert result.returncode != 0, "validator should reject malformed fixture"
        assert "_bogus_invalid.json" in (result.stdout + result.stderr)
    finally:
        bogus.unlink(missing_ok=True)
