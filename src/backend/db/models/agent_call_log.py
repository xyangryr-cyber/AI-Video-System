"""Pydantic model for ``agent_call_log`` rows (SPEC-B-007)."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class AgentCallLogEntry(BaseModel):
    id: Optional[int] = None
    agent_name: str
    tokens: int = Field(gt=0)
    duration_ms: int = Field(gt=0)
    phase: Optional[int] = None
    project_id: Optional[str] = None
    model: str
    prompt: str
    response: str
    created_at: str
