"""Pydantic model for ``agent_call_log`` rows (SPEC-B-007)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AgentCallLogEntry(BaseModel):
    id: int | None = None
    agent_name: str
    tokens: int = Field(gt=0)
    duration_ms: int = Field(gt=0)
    phase: int | None = None
    project_id: str | None = None
    model: str
    prompt: str
    response: str
    created_at: str
