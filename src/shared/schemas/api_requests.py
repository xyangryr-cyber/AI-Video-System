"""[SPEC-A-006] Pydantic request schemas for SPEC-1A REST endpoints.

Authority: docs/specs/SPEC-A-contracts.md SPEC-1A.

Every mutating endpoint (POST/PUT) whose body is non-empty has a
request model here. GET/DELETE routes (no body) and the three bodyless
mutating routes (`/skip`, `/tasks/{id}/cancel`,
`/preferences/snapshots/{id}/rollback`) have no entry in this module.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class CreateProjectRequest(_Strict):
    """POST /api/projects body. Description min length 10 per SPEC-1A."""

    title: str = Field(min_length=1)
    description: str = Field(min_length=10)


class AdvanceRequest(_Strict):
    """POST /api/projects/{id}/advance body.

    `confirmed_preferences` is optional -- the frontend sends it when the
    user has just resolved P5/P6/P7 candidate confirmations inline with
    the advance request; otherwise the field is omitted.
    """

    confirmed_preferences: Optional[List[Dict[str, Any]]] = None


class RollbackRequest(_Strict):
    """POST /api/projects/{id}/rollback body."""

    target_phase: int = Field(ge=0, le=11)


class ChatRequest(_Strict):
    """POST /api/projects/{id}/chat body."""

    message: str = Field(min_length=1)


class PreferenceDecision(_Strict):
    """Per-candidate decision inside PreferencesConfirmRequest."""

    id: str = Field(min_length=1)
    action: str = Field(min_length=1)
    text: Optional[str] = None


class PreferencesConfirmRequest(_Strict):
    """POST /api/projects/{id}/preferences/confirm body."""

    decisions: List[PreferenceDecision]


__all__ = [
    "AdvanceRequest",
    "ChatRequest",
    "CreateProjectRequest",
    "PreferenceDecision",
    "PreferencesConfirmRequest",
    "RollbackRequest",
]
