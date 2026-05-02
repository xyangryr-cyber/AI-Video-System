"""[SPEC-D-012] Tests: content quality gate — placeholder text, uniform frames, duration deviation.

Authority: task card SPEC-D-012.
"""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest
from PIL import Image

from src.backend.engine import gatekeeper as gk_mod

# -- Schema path for in-memory DB fixture --------------------------------

SCHEMA_PATH = Path(__file__).resolve().parents[4] / "src" / "backend" / "db" / "schema.sql"


@pytest.fixture()
def conn() -> sqlite3.Connection:
    """In-memory DB with full schema."""
    c = sqlite3.connect(":memory:")
    c.execute("PRAGMA foreign_keys = ON")
    c.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))
    return c


def _seed_project(conn: sqlite3.Connection, pid: str = "proj_1") -> str:
    conn.execute(
        "INSERT INTO projects(project_id, title, description) VALUES(?,?,?)",
        (pid, "t", "desc at least ten chars"),
    )
    conn.commit()
    return pid


def _seed_phase(
    conn: sqlite3.Connection,
    pid: str,
    phase_num: int = 0,
    *,
    artifact_path: str | None = "/tmp/a.json",
    artifact_status: str | None = "ok",
    artifact_version: int = 1,
    preferences_confirmed_at: str | None = "2026-04-23T00:00:00.000Z",
) -> None:
    conn.execute(
        "INSERT INTO phases(project_id, phase_num, phase_name, status, "
        "artifact_version, artifact_status, artifact_path, "
        "preferences_confirmed_at) VALUES(?,?,?,?,?,?,?,?)",
        (
            pid, phase_num, f"P{phase_num}", "active",
            artifact_version, artifact_status, artifact_path,
            preferences_confirmed_at,
        ),
    )
    conn.commit()


def _seed_review(
    conn: sqlite3.Connection,
    pid: str,
    phase_num: int,
    *,
    target_version: int,
    status: str = "succeeded",
    verdict: str = "PASS",
    task_id: str = "t_000001",
) -> None:
    result_ref = json.dumps({"verdict": verdict, "blocking_issues": []})
    conn.execute(
        "INSERT INTO task_ledger(id, project_id, phase, type, status, "
        "target_version, params, result_ref) VALUES(?,?,?,?,?,?,?,?)",
        (task_id, pid, phase_num, "review", status, target_version, "{}", result_ref),
    )
    conn.commit()


def _seed_cost(conn: sqlite3.Connection, pid: str, phase_num: int) -> None:
    conn.execute(
        "INSERT INTO agent_call_log(agent_name, tokens, duration_ms, phase, "
        "project_id, model, prompt, response) VALUES(?,?,?,?,?,?,?,?)",
        ("Producer", 100, 50, phase_num, pid, "claude-sonnet", "p", "r"),
    )
    conn.commit()


def _all_green(conn: sqlite3.Connection, pid: str = "proj_1", phase: int = 0) -> None:
    _seed_project(conn, pid)
    _seed_phase(conn, pid, phase)
    _seed_review(conn, pid, phase, target_version=1)
    _seed_cost(conn, pid, phase)


def _gk(conn: sqlite3.Connection) -> gk_mod.GateKeeper:
    return gk_mod.GateKeeper(conn)


# ========================================================================
# Pure function tests — RED (detectors)
# ========================================================================


class TestDetectPlaceholderText:
    """RED: detect_placeholder_text must find known placeholder patterns."""

    def test_finds_key_point_placeholder(self) -> None:
        """Artifact containing 'Key point 1 for hook' returns non-empty list."""
        from src.backend.gates.content_quality_checks import detect_placeholder_text

        artifact = {"text": "Here is Key point 1 for hook in the script."}
        results = detect_placeholder_text(artifact)
        assert len(results) > 0, f"should find placeholder; got {results}"
        assert "Key point 1 for hook" in results

    def test_finds_multiple_patterns(self) -> None:
        """Multiple placeholder patterns in one text are all detected."""
        from src.backend.gates.content_quality_checks import detect_placeholder_text

        artifact = {
            "text": (
                "Key point 3 for intro. Then market data point 5 is shown. "
                "Finally Transition from intro to body occurs."
            )
        }
        results = detect_placeholder_text(artifact)
        assert len(results) >= 3, f"should find >=3 placeholders; got {results}"

    def test_clean_text_returns_empty(self) -> None:
        """Text without placeholders returns empty list."""
        from src.backend.gates.content_quality_checks import detect_placeholder_text

        artifact = {"text": "Market rallied 2.3 percent amid strong earnings reports."}
        results = detect_placeholder_text(artifact)
        assert results == []

    def test_empty_text_returns_empty(self) -> None:
        """Empty or missing text returns empty list."""
        from src.backend.gates.content_quality_checks import detect_placeholder_text

        assert detect_placeholder_text({}) == []
        assert detect_placeholder_text({"text": ""}) == []


class TestDetectUniformColorFrame:
    """RED: detect_uniform_color_frame must detect solid-color images."""

    def test_solid_color_image_returns_true(self) -> None:
        """A pure red 100x100 image has std < 10 and returns True."""
        from src.backend.gates.content_quality_checks import detect_uniform_color_frame

        arr = np.full((100, 100, 3), 128, dtype=np.uint8)
        img = Image.fromarray(arr)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f, format="PNG")
            tmp_path = f.name

        try:
            result = detect_uniform_color_frame(tmp_path)
            assert result is True, f"solid color should return True; got {result}"
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_normal_image_returns_false(self) -> None:
        """A gradient image with high variance returns False."""
        from src.backend.gates.content_quality_checks import detect_uniform_color_frame

        arr = np.random.randint(0, 256, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(arr)
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            img.save(f, format="PNG")
            tmp_path = f.name

        try:
            result = detect_uniform_color_frame(tmp_path)
            assert result is False, f"noisy image should return False; got {result}"
        finally:
            Path(tmp_path).unlink(missing_ok=True)


class TestDetectDurationDeviation:
    """RED: detect_duration_deviation must flag deviations > 10 percent."""

    def test_large_deviation_returns_true(self) -> None:
        """Duration 600 declared, 82 measured -> (True, ~86.3%)."""
        from src.backend.gates.content_quality_checks import detect_duration_deviation

        artifact = {"duration": 600}
        is_deviation, pct = detect_duration_deviation(artifact, 82.0)
        assert is_deviation is True, f"should detect deviation; got {is_deviation}"
        assert abs(pct - 86.3) < 0.1, f"deviation pct should be ~86.3; got {pct}"

    def test_small_deviation_returns_false(self) -> None:
        """Duration 100 declared, 105 measured -> (False, 5.0%)."""
        from src.backend.gates.content_quality_checks import detect_duration_deviation

        artifact = {"duration": 100}
        is_deviation, pct = detect_duration_deviation(artifact, 105.0)
        assert is_deviation is False, f"small deviation should not flag; got {is_deviation}"
        assert abs(pct - 5.0) < 0.1, f"deviation pct should be ~5.0; got {pct}"

    def test_zero_duration_handled(self) -> None:
        """Zero declared duration returns (False, 0.0)."""
        from src.backend.gates.content_quality_checks import detect_duration_deviation

        artifact = {"duration": 0}
        is_deviation, pct = detect_duration_deviation(artifact, 10.0)
        assert is_deviation is False
        assert pct == 0.0


# ========================================================================
# GateKeeper integration tests — RED
# ========================================================================


class TestGateKeeperContentQualityIntegration:
    """Verify GateKeeper dispatches content quality checks and propagates failures."""

    def test_gate_fails_when_placeholder_text_detected(self, conn: sqlite3.Connection) -> None:
        """P0 phase with placeholder text should fail the gate."""
        _all_green(conn, "proj_1", 0)
        gk = _gk(conn)

        fake_placeholder = ["Key point 1 for hook"]
        with patch(
            "src.backend.gates.content_quality_checks.detect_placeholder_text",
            return_value=fake_placeholder,
        ):
            result = gk.check("proj_1", 0, mode="advance")

        assert result.passed is False, (
            f"gate should fail when content quality fails; got {result!r}"
        )
        content_checks = [c for c in result.failed_checks if c.check == "content_quality"]
        assert len(content_checks) > 0, (
            f"should have content_quality in failed_checks; got {result.failed_checks}"
        )

    def test_gate_passes_when_no_placeholder_text(self, conn: sqlite3.Connection) -> None:
        """P0 phase with clean text should pass (all other checks green)."""
        _all_green(conn, "proj_1", 0)
        gk = _gk(conn)

        with patch(
            "src.backend.gates.content_quality_checks.detect_placeholder_text",
            return_value=[],
        ):
            result = gk.check("proj_1", 0, mode="advance")

        assert result.passed is True, (
            f"gate should pass when content is clean; got {result!r}"
        )

    def test_gate_fails_when_uniform_color_frame_detected(self, conn: sqlite3.Connection) -> None:
        """P8 phase with solid color should fail the gate."""
        _all_green(conn, "proj_1", 8)
        gk = _gk(conn)

        with patch(
            "src.backend.gates.content_quality_checks.detect_uniform_color_frame",
            return_value=True,
        ):
            result = gk.check("proj_1", 8, mode="advance")

        assert result.passed is False, (
            f"gate should fail for uniform color frame; got {result!r}"
        )
        content_checks = [c for c in result.failed_checks if c.check == "content_quality"]
        assert len(content_checks) > 0

    def test_gate_fails_when_duration_deviation_detected(self, conn: sqlite3.Connection) -> None:
        """P4 phase with duration deviation should fail the gate."""
        _all_green(conn, "proj_1", 4)
        gk = _gk(conn)

        with patch.object(
            gk, "_read_measured_duration_sec", return_value=82.0
        ), patch.object(
            gk, "_load_artifact_declared_duration", return_value=600.0
        ), patch(
            "src.backend.gates.content_quality_checks.detect_duration_deviation",
            return_value=(True, 86.3),
        ):
            result = gk.check("proj_1", 4, mode="advance")

        assert result.passed is False, (
            f"gate should fail for duration deviation; got {result!r}"
        )

    def test_content_quality_not_checked_in_skip_mode(self, conn: sqlite3.Connection) -> None:
        """Skip mode does NOT run content quality checks."""
        _all_green(conn, "proj_1", 0)
        gk = _gk(conn)

        mock_detect = patch(
            "src.backend.gates.content_quality_checks.detect_placeholder_text",
            return_value=["Key point 1 for hook"],
        )
        with mock_detect as m:
            result = gk.check("proj_1", 0, mode="skip")

        m.assert_not_called()
        assert result.passed is True
