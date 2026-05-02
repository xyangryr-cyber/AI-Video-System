"""[SPEC-A-011] Unified API error response schema (SPEC-13A).

Authority: docs/specs/SPEC-A-contracts.md SPEC-13A.

All API error responses MUST conform to ``ErrorResponse`` -- a single
``error`` wrapper containing ``code``, ``message`` and optional ``details``.

Gate failures (HTTP 422 + EVID_2001) MUST NOT short-circuit: the gatekeeper
evaluates every declared check, and every check outcome (passed or failed)
MUST be reported via ``GateFailureDetails.passed_checks`` /
``GateFailureDetails.failed_checks``. See ``GateFailureDetails`` docstring.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class _StrictModel(BaseModel):
    """Base: forbid unknown fields so typos fail loudly."""

    model_config = ConfigDict(extra="forbid")


class ErrorBody(_StrictModel):
    """Inner body of the unified error response envelope.

    Fields:
      - code: an ``EVID_xxxx`` string drawn from
        :class:`src.shared.constants.error_codes.ErrorCode`.
      - message: human-readable description (template placeholders may be
        substituted with concrete values before send).
      - details: optional machine-readable context; for EVID_2001 this MUST
        be a :class:`GateFailureDetails`-shaped object.
    """

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(_StrictModel):
    """Top-level error envelope: ``{error: {code, message, details?}}``."""

    error: ErrorBody


class FailedGateCheck(_StrictModel):
    """A single failed gatekeeper check with a human-readable reason."""

    check: str
    reason: str


class GateFailureDetails(_StrictModel):
    """``details`` payload attached to EVID_2001 (Gate check failed).

    Gate evaluation does NOT short-circuit on the first failure: all declared
    checks are evaluated and every outcome is recorded here. ``failed_checks``
    lists every check that did not pass (with its reason), and
    ``passed_checks`` lists every check that did pass. Together they expose
    the full gate evaluation so the frontend can render a complete fix list
    to the user without another round-trip.
    """

    failed_checks: list[FailedGateCheck]
    passed_checks: list[str]


__all__ = [
    "ErrorBody",
    "ErrorResponse",
    "FailedGateCheck",
    "GateFailureDetails",
]
