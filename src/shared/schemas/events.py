"""[SPEC-A-010] WebSocket event envelope and payload schemas.

Authority: docs/specs/SPEC-A-contracts.md SPEC-11A.

Defines:
  - WsEventEnvelope: unified outer message shape {type, timestamp, project_id, payload}.
  - 17 payload Pydantic models (one per EventType) + EVENT_PAYLOAD_REGISTRY.
  - 2 streaming payloads (StreamTokenPayload, StreamDonePayload) -- NOT in EventType.
  - 1 audit-only payload (PreferenceRollbackPayload) -- NOT in EventType, registered
    in AUDIT_ONLY_EVENTS to mark it as never-broadcast.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, FrozenSet, List, Mapping, Optional, Type

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.shared.constants.event_types import EventType


_ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:\d{2})$"
)


class _StrictModel(BaseModel):
    """Base: forbid unknown fields so typos fail loudly."""

    model_config = ConfigDict(extra="forbid")


# ---- Enums used inside payloads -------------------------------------------


class ReviewVerdict(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


class ReviewLevel(str, Enum):
    L1 = "L1"
    L2 = "L2"


class DamageType(str, Enum):
    TRUNCATED = "truncated"
    CORRUPTED = "corrupted"
    MISSING = "missing"


# ---- The 17 payload models (order = SPEC-11A table) -----------------------


class PhaseEnteredPayload(_StrictModel):
    phase_num: int
    phase_name: str


class PhaseExitedPayload(_StrictModel):
    phase_num: int


class PhaseInvalidatedPayload(_StrictModel):
    phase_num: int
    reason: str


class TaskCreatedPayload(_StrictModel):
    task_id: str
    task_type: str
    phase: int


class TaskQueuedPayload(_StrictModel):
    task_id: str


class TaskStartedPayload(_StrictModel):
    task_id: str
    agent_name: str


class TaskProgressPayload(_StrictModel):
    task_id: str
    progress: int = Field(ge=0, le=100)
    message: Optional[str] = None


class TaskCompletedPayload(_StrictModel):
    task_id: str
    result_ref: Optional[str] = None


class TaskFailedPayload(_StrictModel):
    task_id: str
    error_code: str
    error_message: str


class TaskSupersededPayload(_StrictModel):
    task_id: str
    superseded_by: Optional[str] = None


class ArtifactProducedPayload(_StrictModel):
    phase_num: int
    version: int
    artifact_path: str


class ArtifactDamagedPayload(_StrictModel):
    phase_num: int
    artifact_path: str
    damage_type: DamageType


class ReviewStartedPayload(_StrictModel):
    phase_num: int
    reviewer_name: str
    level: ReviewLevel


class FailedCheck(_StrictModel):
    check_name: str
    reason: str


class ReviewCompletedPayload(_StrictModel):
    phase_num: int
    reviewer_name: str
    verdict: ReviewVerdict
    notes: List[str]
    blocking_issues: List[str]


class GatePassedPayload(_StrictModel):
    phase_num: int


class GateFailedPayload(_StrictModel):
    phase_num: int
    failed_checks: List[FailedCheck]


class PreferenceCandidate(_StrictModel):
    id: str
    rule: str
    confidence: float = Field(ge=0.0, le=1.0)


class PreferenceExtractedPayload(_StrictModel):
    candidates_count: int = Field(ge=0)
    candidates: List[PreferenceCandidate]


# ---- Streaming payloads (NOT in EventType) --------------------------------


class StreamTokenPayload(_StrictModel):
    task_id: str
    token: str
    seq: int = Field(ge=0)


class StreamDonePayload(_StrictModel):
    task_id: str
    full_text: str


# ---- Audit-only payload (NOT in EventType, never broadcast) ---------------


class PreferenceRollbackPayload(_StrictModel):
    snapshot_id: str
    target_snapshot_id: str
    new_snapshot_id: str


# ---- Envelope -------------------------------------------------------------


class WsEventEnvelope(_StrictModel):
    """Unified outer message shape for all WS broadcasts (SPEC-11A)."""

    type: EventType
    timestamp: str
    project_id: str
    payload: Dict[str, Any]

    @field_validator("timestamp")
    @classmethod
    def _validate_iso8601(cls, value: str) -> str:
        if not isinstance(value, str) or not _ISO8601_RE.match(value):
            raise ValueError(f"timestamp must be ISO8601, got {value!r}")
        return value


# ---- REST API list item (distinct from WS envelope) ----------------------


class AgentEventListItem(_StrictModel):
    """Shape of each element in `GET /api/projects/{id}/events` responses.

    Differs from `WsEventEnvelope` in two ways:
      - has an `id` field (DB row id exposed for frontend pagination).
      - `type` is a free-form string (REST endpoint also exposes internal
        event names such as `phase.advanced` / `agent.call` that aren't in
        the 17-type broadcast enum). Strict typing lives on the WS path.
    """

    id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    timestamp: str = Field(min_length=1)
    payload: Dict[str, Any]


# ---- Registry + audit-only list -------------------------------------------

EVENT_PAYLOAD_REGISTRY: Dict[EventType, Type[_StrictModel]] = {
    EventType.PHASE_ENTERED: PhaseEnteredPayload,
    EventType.PHASE_EXITED: PhaseExitedPayload,
    EventType.PHASE_INVALIDATED: PhaseInvalidatedPayload,
    EventType.TASK_CREATED: TaskCreatedPayload,
    EventType.TASK_QUEUED: TaskQueuedPayload,
    EventType.TASK_STARTED: TaskStartedPayload,
    EventType.TASK_PROGRESS: TaskProgressPayload,
    EventType.TASK_COMPLETED: TaskCompletedPayload,
    EventType.TASK_FAILED: TaskFailedPayload,
    EventType.TASK_SUPERSEDED: TaskSupersededPayload,
    EventType.ARTIFACT_PRODUCED: ArtifactProducedPayload,
    EventType.ARTIFACT_DAMAGED: ArtifactDamagedPayload,
    EventType.REVIEW_STARTED: ReviewStartedPayload,
    EventType.REVIEW_COMPLETED: ReviewCompletedPayload,
    EventType.GATE_PASSED: GatePassedPayload,
    EventType.GATE_FAILED: GateFailedPayload,
    EventType.PREFERENCE_EXTRACTED: PreferenceExtractedPayload,
}


AUDIT_ONLY_EVENTS: FrozenSet[str] = frozenset({"preference.rollback"})


def validate_event_payload(
    event_type: EventType, payload: Mapping[str, Any]
) -> _StrictModel:
    """Return the validated Pydantic model instance for `payload` under `event_type`.

    Raises:
        KeyError: when `event_type` has no registered payload model.
        pydantic.ValidationError: when `payload` violates the schema.
    """
    model_cls = EVENT_PAYLOAD_REGISTRY[event_type]
    return model_cls.model_validate(payload)


__all__ = [
    "AUDIT_ONLY_EVENTS",
    "AgentEventListItem",
    "ArtifactDamagedPayload",
    "ArtifactProducedPayload",
    "DamageType",
    "EVENT_PAYLOAD_REGISTRY",
    "FailedCheck",
    "GateFailedPayload",
    "GatePassedPayload",
    "PhaseEnteredPayload",
    "PhaseExitedPayload",
    "PhaseInvalidatedPayload",
    "PreferenceCandidate",
    "PreferenceExtractedPayload",
    "PreferenceRollbackPayload",
    "ReviewCompletedPayload",
    "ReviewLevel",
    "ReviewStartedPayload",
    "ReviewVerdict",
    "StreamDonePayload",
    "StreamTokenPayload",
    "TaskCompletedPayload",
    "TaskCreatedPayload",
    "TaskFailedPayload",
    "TaskProgressPayload",
    "TaskQueuedPayload",
    "TaskStartedPayload",
    "TaskSupersededPayload",
    "WsEventEnvelope",
    "validate_event_payload",
]
