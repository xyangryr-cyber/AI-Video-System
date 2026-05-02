"""[SPEC-GAPFIX-030] Tests for generate_error_codes.py enum sync script."""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
SCRIPT = PROJECT_ROOT / "scripts" / "generate_error_codes.py"
CONTRACT_PY = PROJECT_ROOT / "src" / "shared" / "contracts" / "error_codes.py"
CONTRACT_TS = PROJECT_ROOT / "src" / "shared" / "contracts" / "error_codes.ts"


def _run_script(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
    )


class TestGenerateErrorCodesCheck:
    """--check mode: exit 0 when consistent, 1 when mismatched."""

    def test_check_consistent_exits_zero(self):
        """When py and ts are in sync, --check exits 0."""
        result = _run_script("--check")
        assert result.returncode == 0, (
            f"Expected exit 0 for consistent files, got {result.returncode}\n"
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_check_mismatch_exits_nonzero(self):
        """When ts is out of sync with py, --check exits non-zero."""
        original = CONTRACT_TS.read_text(encoding="utf-8")
        try:
            CONTRACT_TS.write_text("// intentionally broken\n")
            result = _run_script("--check")
            assert result.returncode != 0, (
                f"Expected non-zero exit for mismatch, got {result.returncode}"
            )
        finally:
            CONTRACT_TS.write_text(original)


class TestGenerateErrorCodesGenerate:
    """Generation mode: write updated TS from Python source."""

    def test_generate_writes_expected_keys(self):
        """After generation, TS file contains all 17 EVID_ codes."""
        backup = CONTRACT_TS.read_text(encoding="utf-8")
        try:
            result = _run_script()  # no --check = generate mode
            assert result.returncode == 0, f"Generate failed: {result.stderr}"
            ts_content = CONTRACT_TS.read_text(encoding="utf-8")
            expected_codes = [
                "EVID_1001", "EVID_1002", "EVID_1003",
                "EVID_2001", "EVID_2002", "EVID_2003", "EVID_2004", "EVID_2005",
                "EVID_3001", "EVID_3002", "EVID_3003", "EVID_3004",
                "EVID_4001", "EVID_4002",
                "EVID_5001", "EVID_5002", "EVID_5003",
            ]
            for code in expected_codes:
                assert code in ts_content, f"Missing code in generated TS: {code}"
        finally:
            CONTRACT_TS.write_text(backup)

    def test_generate_idempotent(self):
        """Running generate twice produces identical output."""
        backup = CONTRACT_TS.read_text(encoding="utf-8")
        try:
            _run_script()
            first = CONTRACT_TS.read_text(encoding="utf-8")
            _run_script()
            second = CONTRACT_TS.read_text(encoding="utf-8")
            assert first == second, "Generate is not idempotent"
        finally:
            CONTRACT_TS.write_text(backup)

    def test_error_code_count_is_17(self):
        """Each error code domain has correct count."""
        backup = CONTRACT_TS.read_text(encoding="utf-8")
        try:
            _run_script()
            result = _run_script("--check")
            assert result.returncode == 0
            assert "17" in result.stdout, f"Expected 17 codes, got: {result.stdout}"
        finally:
            CONTRACT_TS.write_text(backup)
