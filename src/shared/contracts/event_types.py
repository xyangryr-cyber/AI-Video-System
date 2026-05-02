"""[SPEC-11A] WebSocket event type enum.

Authority: docs/specs/SPEC-A-contracts.md SPEC-11A "WebSocket Event Envelope & Event Types".

Defines exactly 17 event types covering phase lifecycle, task lifecycle,
artifact tracking, review, gates, and preference extraction.  Downstream
code (event emitters, WS broadcasters, frontend subscribers) MUST use
these enum values rather than hard-coding event type strings.

Values use dot-notation strings as specified in SPEC-11A.
"""

from __future__ import annotations

from enum import Enum


class EventType(str, Enum):
    """WebSocket event types per SPEC-11A."""

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
