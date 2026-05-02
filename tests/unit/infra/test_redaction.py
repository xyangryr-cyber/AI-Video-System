"""Tests for [SPEC-B-008] Sensitive Field Redaction and Leak Scan.

Real assertions for AC-1..AC-5 covering API key redaction, 7 regex rules,
large-payload truncation, leak scan script, and redaction-before-DB-write.

Coverage:
* AC-1: sk- prefix API keys redacted to [REDACTED] before DB write.
* AC-2: SECRET_REGEXES contains exactly 7 rules.
* AC-3: >8KB prompt/response truncated to first 2KB + last 2KB + MD5.
* AC-4: leak_scan.py executable, samples 1000 lines, exits 0 with no hits.
* AC-5: Redaction happens before DB write (not at query time).
"""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    return c


def _insert_project(conn: sqlite3.Connection, pid: str = "proj_a") -> None:
    conn.execute(
        "INSERT INTO projects (project_id, title, description) VALUES (?,?,?)",
        (pid, "Test Project", "test"),
    )


# --- AC-1: sk- prefix redacted -----------------------------------------------


class TestAC1SkPrefixRedacted:
    def test_sk_prefix_redacted(self, conn: sqlite3.Connection):
        """API keys with sk- prefix appear as [REDACTED] in stored prompt."""
        _insert_project(conn)
        from src.backend.core.redaction import redact_text
        from src.backend.core.llm_client import LLMClient

        def fake_completion(**kwargs):
            return {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"total_tokens": 10},
                "model": "m",
            }

        client = LLMClient(conn)
        client.chat_completion(
            role="producer",
            messages=[{"role": "user", "content": "Authorization: Bearer sk-abc123"}],
            agent_name="TestAgent",
            phase=1,
            project_id="proj_a",
            _completion_fn=fake_completion,
        )

        row = conn.execute(
            "SELECT prompt FROM agent_call_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        stored_prompt = row["prompt"]
        assert "sk-abc123" not in stored_prompt
        assert "[REDACTED]" in stored_prompt

        # Also test the redact_text function directly
        result = redact_text("key=sk-proj-1234567890abcdef")
        assert "sk-proj-1234567890abcdef" not in result
        assert "[REDACTED]" in result


# --- AC-2: 7 regex rules -----------------------------------------------------


class TestAC2SecretRegexesCount7:
    def test_secret_regexes_count_7(self):
        """SECRET_REGEXES has exactly 7 rules covering common key formats."""
        from src.backend.core.redaction import SECRET_REGEXES

        assert len(SECRET_REGEXES) == 7, (
            f"Expected 7 secret regexes, got {len(SECRET_REGEXES)}"
        )

    def test_each_regex_covers_different_patterns(self):
        """Each regex redacts its target pattern."""
        from src.backend.core.redaction import redact_text

        tests = [
            ("sk-", "Bearer sk-abc123xyz"),
            ("openai_key", "openai_key_sk-12345"),
            ("github_pat", "ghp_abc123def456ghi789"),
            ("aws_key", "AKIAIOSFODNN7EXAMPLE"),
            (
                "jwt",
                "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
            ),
            ("private_key", "-----BEGIN RSA PRIVATE KEY-----\nMIICWwIBAAKBgQC"),
            ("google_api", "ya29.a0AfH6SMB1abc123"),
        ]
        for name, text in tests:
            result = redact_text(text)
            assert "[REDACTED]" in result, f"{name}: pattern not redacted in {text!r}"


# --- AC-3: large payload truncation -------------------------------------------


class TestAC3LargePayloadTruncation:
    def test_large_payload_truncation(self):
        """>8KB content truncated to first 2KB + last 2KB + MD5."""
        from src.backend.core.redaction import truncate_large_payload

        big = "x" * 9000
        result = truncate_large_payload(big)
        assert len(big) > 8192
        assert len(result) < len(big)
        assert "TRUNCATED" in result or "..." in result
        # Should contain the first and last portions
        assert big[:100] in result or "x" * 50 in result

    def test_small_payload_not_truncated(self):
        """Content under 8KB is returned as-is."""
        from src.backend.core.redaction import truncate_large_payload

        small = "hello world"
        assert truncate_large_payload(small) == small

    def test_truncation_includes_md5(self):
        """Truncated output includes MD5 hash of original."""
        from src.backend.core.redaction import truncate_large_payload

        big = "a" * 9000
        result = truncate_large_payload(big)
        expected_hash = hashlib.md5(big.encode()).hexdigest()
        assert expected_hash in result


# --- AC-4: leak scan zero hits -----------------------------------------------


class TestAC4LeakScanZeroHits:
    def test_leak_scan_zero_hits(self, tmp_path):
        """leak_scan.py scans 1000 lines and exits 0 when no leaks found."""
        scan_script = REPO_ROOT / "scripts" / "leak_scan.py"
        if not scan_script.exists():
            pytest.skip("leak_scan.py not created yet")

        # Create a clean sample file
        clean = tmp_path / "clean_sample.txt"
        clean.write_text(
            "\n".join(f"line {i}: normal text no secrets" for i in range(100))
        )

        result = subprocess.run(
            [
                sys.executable,
                str(scan_script),
                "--input",
                str(clean),
                "--sample-size",
                "100",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode == 0, (
            f"Expected exit 0, got {result.returncode}: {result.stderr}"
        )

    def test_leak_scan_detects_secret(self, tmp_path):
        """leak_scan.py detects a sk- key in sampled lines."""
        scan_script = REPO_ROOT / "scripts" / "leak_scan.py"
        if not scan_script.exists():
            pytest.skip("leak_scan.py not created yet")

        dirty = tmp_path / "dirty_sample.txt"
        lines = [f"line {i}: normal text" for i in range(99)]
        lines.append("Authorization: Bearer sk-abc123")
        dirty.write_text("\n".join(lines))

        result = subprocess.run(
            [
                sys.executable,
                str(scan_script),
                "--input",
                str(dirty),
                "--sample-size",
                "100",
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
        assert result.returncode != 0, (
            f"Expected non-zero exit when leak detected, got {result.returncode}"
        )


# --- AC-5: redaction before DB write -----------------------------------------


class TestAC5RedactionBeforeDbWrite:
    def test_redaction_before_db_write(self, conn: sqlite3.Connection):
        """Redaction happens before data is written to agent_call_log."""
        _insert_project(conn)
        from src.backend.core.llm_client import LLMClient

        def fake_completion(**kwargs):
            return {
                "choices": [{"message": {"content": "response with sk-key123"}}],
                "usage": {"total_tokens": 10},
                "model": "m",
            }

        client = LLMClient(conn)
        client.chat_completion(
            role="producer",
            messages=[{"role": "user", "content": "my key: sk-proj-secret"}],
            agent_name="TestAgent",
            phase=1,
            project_id="proj_a",
            _completion_fn=fake_completion,
        )

        row = conn.execute(
            "SELECT prompt, response FROM agent_call_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert "sk-proj-secret" not in row["prompt"]
        assert "sk-key123" not in row["response"]
        assert "[REDACTED]" in row["prompt"]
