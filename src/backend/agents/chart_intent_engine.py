"""[SPEC-C-105] ChartIntentEngine 8-state machine (v3.16 C-BDD-6).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-6 (SPEC-6.V).

Eight states and exactly ten legal transitions form the ChartRequest
lifecycle. Any other ``(from, to)`` pair raises
``IllegalChartStateTransition`` -- there are no self-loops, no backward
edges, and no path from ``fetching`` directly into ``rendering`` (AC-4).

The engine is stateless: all methods are pure functions of their inputs,
so callers persist the ``ChartRequest.status`` transitions themselves
and the matrix alone drives legality. Clarification priority and
chart-bound claim aggregation are the two domain-specific policies the
engine owns on top of the bare matrix.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

CHART_STATES: tuple[str, ...] = (
    "awaiting_clarification",
    "fetching",
    "awaiting_verification",
    "awaiting_confirmation",
    "rendering",
    "completed",
    "failed",
    "cancelled",
)

TERMINAL_STATES: frozenset[str] = frozenset({"completed", "failed", "cancelled"})

# SPEC §C-BDD-6 transition graph -- exactly 10 edges.
LEGAL_EDGES: frozenset[tuple[str, str]] = frozenset(
    {
        ("awaiting_clarification", "fetching"),
        ("awaiting_clarification", "cancelled"),
        ("fetching", "awaiting_verification"),
        ("fetching", "failed"),
        ("awaiting_verification", "awaiting_confirmation"),
        ("awaiting_verification", "failed"),
        ("awaiting_confirmation", "rendering"),
        ("awaiting_confirmation", "cancelled"),
        ("rendering", "completed"),
        ("rendering", "failed"),
    }
)

# SPEC §C-BDD-6 "澄清字段优先级":
# time_range/granularity > entity > unit/comparison_targets.
CLARIFICATION_PRIORITY: tuple[str, ...] = (
    "time_range",
    "granularity",
    "entity",
    "unit",
    "comparison_targets",
)

MAX_CLARIFICATIONS_PER_ROUND: int = 2


class IllegalChartStateTransition(Exception):
    """Raised when a ChartRequest status change is not in ``LEGAL_EDGES``."""

    def __init__(self, from_state: str, to_state: str) -> None:
        self.from_state = from_state
        self.to_state = to_state
        super().__init__(f"Illegal chart state transition: {from_state!r} -> {to_state!r}")


def _is_missing(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, (str, list, tuple, dict, set)) and len(value) == 0:
        return True
    return False


class ChartIntentEngine:
    """Stateless policy for chart-intent status transitions."""

    STATES = CHART_STATES
    LEGAL_EDGES = LEGAL_EDGES
    TERMINAL_STATES = TERMINAL_STATES
    CLARIFICATION_PRIORITY = CLARIFICATION_PRIORITY
    MAX_CLARIFICATIONS_PER_ROUND = MAX_CLARIFICATIONS_PER_ROUND

    def assert_legal_transition(self, from_state: str, to_state: str) -> None:
        """Raise ``IllegalChartStateTransition`` unless edge is in matrix."""
        if (from_state, to_state) not in LEGAL_EDGES:
            raise IllegalChartStateTransition(from_state, to_state)

    def next_clarification_fields(self, request: Mapping[str, Any]) -> list[str]:
        """Return up to ``MAX_CLARIFICATIONS_PER_ROUND`` missing fields.

        Fields are returned in SPEC priority order; ``None`` / empty
        string / empty list count as missing.
        """
        missing: list[str] = []
        for field in CLARIFICATION_PRIORITY:
            if _is_missing(request.get(field)):
                missing.append(field)
                if len(missing) >= MAX_CLARIFICATIONS_PER_ROUND:
                    break
        return missing

    def advance_after_verification(
        self,
        chart_bound_claims: Sequence[Mapping[str, Any]],
    ) -> str:
        """Decide the next status from the set of chart-bound claims.

        - Any claim ``status == 'rejected'`` -> ``failed`` (verifier FAIL).
        - Every claim ``status == 'verified'`` -> ``awaiting_confirmation``
          (verifier PASS).
        - Empty set or any non-terminal status (``pending`` /
          ``user_disputed`` / etc.) -> ``awaiting_verification`` (hold).
        """
        if not chart_bound_claims:
            return "awaiting_verification"
        has_pending = False
        for claim in chart_bound_claims:
            status = claim.get("status")
            if status == "rejected":
                return "failed"
            if status != "verified":
                has_pending = True
        if has_pending:
            return "awaiting_verification"
        return "awaiting_confirmation"

    def handle_fetch_result(self, *, data_source_available: bool) -> str:
        """Exit status from ``fetching``.

        - ``True``  -> ``awaiting_verification``.
        - ``False`` -> ``failed`` (never cascade through rendering).
        """
        return "awaiting_verification" if data_source_available else "failed"


__all__ = [
    "CHART_STATES",
    "CLARIFICATION_PRIORITY",
    "ChartIntentEngine",
    "IllegalChartStateTransition",
    "LEGAL_EDGES",
    "MAX_CLARIFICATIONS_PER_ROUND",
    "TERMINAL_STATES",
]
