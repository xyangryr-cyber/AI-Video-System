"""[SPEC-A-006] Pydantic response schemas for SPEC-1A REST endpoints.

Authority: docs/specs/SPEC-A-contracts.md SPEC-1A.

Every 200-OK endpoint body has a response model here. Error responses
use the unified :class:`src.shared.schemas.error_response.ErrorResponse`
(SPEC-A-011 / SPEC-13A).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class OkResponse(_Strict):
    """Generic ``{ok: true}`` ack for side-effect-only endpoints."""

    ok: bool = True


class CreateProjectResponse(_Strict):
    project_id: str = Field(min_length=1)


class AdvanceResponse(_Strict):
    phase: int = Field(ge=0, le=11)
    gate_result: dict[str, Any]


class SkipResponse(_Strict):
    phase: int = Field(ge=0, le=11)


class RollbackResponse(_Strict):
    phase: int = Field(ge=0, le=11)
    invalidated_phases: list[int]


class ChatResponse(_Strict):
    action: str = Field(min_length=1)
    response: str
    details: dict[str, Any] | None = None


class PreferencesConfirmResponse(_Strict):
    ok: bool = True


class PreferencesUpdateResponse(_Strict):
    ok: bool = True
    snapshot_id: str = Field(min_length=1)


class SnapshotRollbackResponse(_Strict):
    ok: bool = True
    new_snapshot_id: str = Field(min_length=1)


class CostsResponse(_Strict):
    total_cost_usd: float = Field(ge=0)
    by_phase: dict[str, float]


class EventsResponse(_Strict):
    events: list[dict[str, Any]]


__all__ = [
    "AdvanceResponse",
    "ChatResponse",
    "CostsResponse",
    "CreateProjectResponse",
    "EventsResponse",
    "OkResponse",
    "PreferencesConfirmResponse",
    "PreferencesUpdateResponse",
    "RollbackResponse",
    "SkipResponse",
    "SnapshotRollbackResponse",
]
