"""[SPEC-A-010] EventType enum -- the 17 WebSocket broadcast event types.

Authority: docs/specs/SPEC-A-contracts.md SPEC-11A.

The enum is exactly 17 values. Streaming events (stream.token, stream.done)
and the audit-only preference.rollback event are defined separately in
src/shared/schemas/events.py; they MUST NOT appear here.
"""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    """The 17 canonical WebSocket broadcast event types (order = spec order)."""

    PHASE_ENTERED = "phase.entered"
    PHASE_EXITED = "phase.exited"
    PHASE_INVALIDATED = "phase.invalidated"
    TASK_CREATED = "task.created"
    TASK_QUEUED = "task.queued"
    TASK_STARTED = "task.started"
    TASK_PROGRESS = "task.progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_SUPERSEDED = "task.superseded"
    ARTIFACT_PRODUCED = "artifact.produced"
    ARTIFACT_DAMAGED = "artifact.damaged"
    REVIEW_STARTED = "review.started"
    REVIEW_COMPLETED = "review.completed"
    GATE_PASSED = "gate.passed"
    GATE_FAILED = "gate.failed"
    PREFERENCE_EXTRACTED = "preference.extracted"


__all__ = ["EventType"]
