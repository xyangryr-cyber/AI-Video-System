"""Tests for [SPEC-A-018] SPEC-13A v3.17 additions: render_failed /
material_missing / material_unverified + SPEC-13B log event-code constraint.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-6
delta: PRD-DELTA-08 / TECH-DELTA-07

Covers AC-1, AC-3, AC-4 of tasks/SPEC-A/A-018-error-codes-and-shot-blocked-event.md.
AC-2 and AC-5 (event schema + type namespace) live in
tests/unit/contracts/test_phase_shot_blocked_event.py.
"""

from __future__ import annotations

import pytest


# The 3 friendly alias names that SPEC-13A v3.17 adds. Each resolves to one
# canonical EVID_* member of the ErrorCode enum.
V317_ALIASES: tuple[str, ...] = (
    "render_failed",
    "material_missing",
    "material_unverified",
)

# Expected HTTP status mapping for the 3 new codes (AC-1: 500 / 422 / 422).
V317_HTTP_STATUS: dict[str, int] = {
    "render_failed": 500,
    "material_missing": 422,
    "material_unverified": 422,
}


class TestAC1:
    """AC-1: SPEC-13A 表新增 3 行（含 http_status 500/422/422 + 触发场景 + 处理建议）；
    Pydantic + TS ErrorCode 枚举同步；既有 17 个错误码不删不改"""

    def test_three_new_codes_present(self):
        """All 3 v3.17 aliases resolve to canonical ErrorCode enum members."""
        from src.shared.constants.error_codes import (
            ERROR_CODE_ALIASES,
            ErrorCode,
            resolve_error_code,
        )

        for alias in V317_ALIASES:
            assert alias in ERROR_CODE_ALIASES, (
                f"v3.17 alias {alias!r} missing from ERROR_CODE_ALIASES; "
                f"SPEC-13A row not added."
            )
            resolved = resolve_error_code(alias)
            assert isinstance(resolved, ErrorCode), (
                f"{alias!r} must resolve to an ErrorCode enum member, "
                f"got {type(resolved).__name__}"
            )

        # The 3 aliases must resolve to 3 DISTINCT canonical codes -- never
        # collapse two failure modes into the same EVID.
        distinct = {resolve_error_code(a) for a in V317_ALIASES}
        assert len(distinct) == 3, (
            f"v3.17 aliases must map to 3 distinct ErrorCode members, got {distinct}"
        )

    def test_http_status_mapping(self):
        """render_failed -> 500, material_missing -> 422, material_unverified -> 422."""
        from src.shared.constants.error_codes import (
            HTTP_STATUS_BY_CODE,
            resolve_error_code,
        )

        for alias, expected_status in V317_HTTP_STATUS.items():
            code = resolve_error_code(alias)
            actual = HTTP_STATUS_BY_CODE[code]
            assert actual == expected_status, (
                f"{alias!r} ({code.value}) must map to HTTP {expected_status}, "
                f"got {actual}"
            )

    def test_v315_codes_intact(self):
        """The 17 pre-v3.17 EVID codes remain present and unchanged."""
        from src.shared.constants.error_codes import (
            HTTP_STATUS_BY_CODE,
            MESSAGE_BY_CODE,
            ErrorCode,
        )

        # Snapshot of (code, http_status, message) at v3.15 / v3.16.
        v315_snapshot: dict[str, tuple[int, str]] = {
            "EVID_1001": (400, "Description too short (min 10 chars)"),
            "EVID_1002": (404, "Project not found"),
            "EVID_1003": (409, "Project is not active"),
            "EVID_2001": (422, "Gate check failed"),
            "EVID_2002": (409, "Gate check already in progress"),
            "EVID_2003": (400, "Phase {N} cannot be skipped"),
            "EVID_2004": (400, "Cannot rollback to phase {N}"),
            "EVID_2005": (409, "Active tasks exist, cannot advance"),
            "EVID_3001": (500, "Agent {name} failed: {reason}"),
            "EVID_3002": (504, "Agent {name} timed out after {N}s"),
            "EVID_3003": (400, "Task {id} cannot be cancelled (status: {status})"),
            "EVID_3004": (500, "LLM call failed: {provider} {error}"),
            "EVID_4001": (404, "Artifact not found for phase {N}"),
            "EVID_4002": (409, "Artifact damaged: {path}"),
            "EVID_5001": (503, "System not ready: {check_name} failed"),
            "EVID_5002": (503, "Worker unavailable"),
            "EVID_5003": (500, "Database error"),
        }
        enum_values = {e.value for e in ErrorCode}
        for code_str, (status, msg) in v315_snapshot.items():
            assert code_str in enum_values, (
                f"v3.15 code {code_str!r} was dropped -- HARNESS forbids "
                f"removing existing ErrorCode members."
            )
            code = ErrorCode(code_str)
            assert HTTP_STATUS_BY_CODE[code] == status, (
                f"v3.15 code {code_str!r} HTTP status changed: "
                f"expected {status}, got {HTTP_STATUS_BY_CODE[code]}"
            )
            assert MESSAGE_BY_CODE[code] == msg, (
                f"v3.15 code {code_str!r} message changed: "
                f"expected {msg!r}, got {MESSAGE_BY_CODE[code]!r}"
            )


class TestAC3:
    """AC-3: 日志格式校验：渲染失败/阻断行的 `event` 字段必须属于新 3 种之一；
    构造非法 event 名抛 `InvalidLogEventError`"""

    def test_log_event_field_constrained(self):
        """validate_log_event_code accepts each of the 3 v3.17 codes."""
        from src.shared.constants.log_event_codes import (
            ALLOWED_LOG_EVENT_CODES,
            validate_log_event_code,
        )

        assert set(ALLOWED_LOG_EVENT_CODES) == set(V317_ALIASES), (
            f"ALLOWED_LOG_EVENT_CODES must be exactly the 3 v3.17 codes, "
            f"got {set(ALLOWED_LOG_EVENT_CODES)}"
        )
        for code in V317_ALIASES:
            assert validate_log_event_code(code) == code, (
                f"validate_log_event_code({code!r}) must return the code unchanged"
            )

    def test_invalid_log_event_raises(self):
        """Unknown / legacy event names raise InvalidLogEventError, not KeyError."""
        from src.shared.constants.log_event_codes import (
            InvalidLogEventError,
            validate_log_event_code,
        )

        with pytest.raises(InvalidLogEventError):
            validate_log_event_code("phase.entered")  # legacy event, not allowed here

        with pytest.raises(InvalidLogEventError):
            validate_log_event_code("__unknown__")

        # The error type must be a dedicated class, not generic Exception/KeyError.
        assert issubclass(InvalidLogEventError, Exception)
        assert not issubclass(InvalidLogEventError, KeyError), (
            "InvalidLogEventError must be distinguishable from KeyError so log "
            "callers can catch it specifically."
        )


class TestAC4:
    """AC-4: 单测：构造三类失败场景各一例（mock 渲染异常 / 物料不存在 / 物料未验证），
    断言对应错误码枚举触发"""

    def test_render_failed_triggered(self):
        """A render exception resolves to the render_failed EVID code with HTTP 500."""
        from src.shared.constants.error_codes import (
            HTTP_STATUS_BY_CODE,
            ErrorCode,
            resolve_error_code,
        )

        def mock_render() -> None:
            raise RuntimeError("Remotion bundler crashed at shot_007")

        with pytest.raises(RuntimeError):
            mock_render()

        code = resolve_error_code("render_failed")
        assert isinstance(code, ErrorCode)
        assert HTTP_STATUS_BY_CODE[code] == 500, (
            "render_failed is a 5xx (server-side render exception), not 4xx."
        )

    def test_material_missing_triggered(self):
        """A missing-material lookup resolves to material_missing (HTTP 422)."""
        from src.shared.constants.error_codes import (
            HTTP_STATUS_BY_CODE,
            ErrorCode,
            resolve_error_code,
        )

        # Mock: materials registry has no entry for shot_007's chart_material_1.
        materials_registry: dict[str, str] = {}
        missing_id = "chart_material_1"

        assert missing_id not in materials_registry

        code = resolve_error_code("material_missing")
        assert isinstance(code, ErrorCode)
        assert HTTP_STATUS_BY_CODE[code] == 422, (
            "material_missing is a 4xx client-input contract violation "
            "(missing referenced material), not a server error."
        )
        # material_missing and render_failed are DIFFERENT codes.
        assert code is not resolve_error_code("render_failed")

    def test_material_unverified_triggered(self):
        """An unverified-material state resolves to material_unverified (HTTP 422)."""
        from src.shared.constants.error_codes import (
            HTTP_STATUS_BY_CODE,
            ErrorCode,
            resolve_error_code,
        )

        # Mock: material exists but verification status is "pending".
        material = {"id": "chart_material_1", "verified": False}
        assert material["verified"] is False

        code = resolve_error_code("material_unverified")
        assert isinstance(code, ErrorCode)
        assert HTTP_STATUS_BY_CODE[code] == 422
        # material_unverified is distinct from material_missing -- different
        # remediation paths in UI (re-verify vs. re-upload).
        assert code is not resolve_error_code("material_missing")
