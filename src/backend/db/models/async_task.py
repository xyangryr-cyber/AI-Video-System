"""Pydantic model for ``async_tasks`` rows (SPEC-B-004).

Mirrors the DDL in ``src/backend/db/schema.sql``; consumers of the
repository + API use this type instead of raw dicts.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AsyncTaskStatus = Literal["pending", "queued", "running", "succeeded", "failed", "cancelled"]


class AsyncTask(BaseModel):
    task_id: str
    project_id: str
    phase: int
    ledger_task_id: str | None = None
    type: str
    params: dict[str, Any] = Field(default_factory=dict)
    status: AsyncTaskStatus = "pending"
    progress: int = Field(default=0, ge=0, le=100)
    worker_id: str | None = None
    attempt: int = 1
    max_attempts: int = 3
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None
    created_at: str
