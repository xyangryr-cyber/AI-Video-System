"""[SPEC-C-002] Task state machine -- SPEC-3.6 transition matrix.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.6.

The matrix enumerates the 10 legal (from, to) transitions. Any other
``task_ledger.status`` change raises :class:`IllegalStateTransition`.
``WorkflowEngine.update_task_status`` calls :func:`ensure_legal_transition`
before any DB write so no invalid row can be persisted.

Each legal target maps to exactly one WS event type (SPEC-11A):
  - ``queued``      -> ``task.queued``
  - ``running``     -> ``task.started``
  - ``succeeded``   -> ``task.completed``
  - ``failed``      -> ``task.failed``
  - ``superseded``  -> ``task.superseded``
  - ``timeout``     -> ``task.failed`` (no dedicated event type in SPEC-11A;
                      reported as a task failure with error_code='TIMEOUT').
"""

from __future__ import annotations

from collections.abc import Mapping

from src.shared.constants.event_types import EventType


class IllegalStateTransition(Exception):
    """Raised when a task_ledger.status change is not in the SPEC-3.6 matrix."""

    def __init__(self, from_status: str, to_status: str) -> None:
        self.from_status = from_status
        self.to_status = to_status
        super().__init__(f"Illegal task status transition: {from_status!r} -> {to_status!r}")


# SPEC-3.6 transition matrix -- exactly 10 legal edges.
LEGAL_TRANSITIONS: frozenset[tuple[str, str]] = frozenset(
    {
        ("pending", "queued"),
        ("pending", "superseded"),
        ("pending", "failed"),
        ("queued", "running"),
        ("queued", "superseded"),
        ("queued", "failed"),
        ("running", "succeeded"),
        ("running", "failed"),
        ("running", "superseded"),
        ("running", "timeout"),
    }
)


# Destination-state -> WS event type emitted on the transition.
EVENT_FOR_TARGET: Mapping[str, EventType] = {
    "queued": EventType.TASK_QUEUED,
    "running": EventType.TASK_STARTED,
    "succeeded": EventType.TASK_COMPLETED,
    "failed": EventType.TASK_FAILED,
    "superseded": EventType.TASK_SUPERSEDED,
    "timeout": EventType.TASK_FAILED,
}


def ensure_legal_transition(from_status: str, to_status: str) -> None:
    """Raise :class:`IllegalStateTransition` unless ``(from, to)`` is legal.

    ``from == to`` is rejected -- SPEC-3.6 has no self-loops and the caller
    should no-op before invoking the engine rather than re-emit events.
    """
    if (from_status, to_status) in LEGAL_TRANSITIONS:
        return
    raise IllegalStateTransition(from_status, to_status)


def event_type_for_target(to_status: str) -> EventType:
    """Return the WS event emitted on a transition into ``to_status``.

    Raises ``KeyError`` for non-destination states (``pending``).
    """
    return EVENT_FOR_TARGET[to_status]


__all__ = [
    "EVENT_FOR_TARGET",
    "IllegalStateTransition",
    "LEGAL_TRANSITIONS",
    "ensure_legal_transition",
    "event_type_for_target",
]
