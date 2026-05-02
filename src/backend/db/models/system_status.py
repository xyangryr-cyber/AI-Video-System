"""Pydantic model for ``system_status`` rows (SPEC-B-009).

Mirrors the DDL in ``src/backend/db/schema.sql`` / SPEC-A SPEC-1B.
Used to shape the ``/api/system/status`` response and anywhere the
Pre-flight layer passes a check record around as structured data rather
than a raw :class:`sqlite3.Row`.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

SystemCheckStatus = Literal["ok", "degraded", "failed"]


class SystemStatusRow(BaseModel):
    id: int | None = None
    check_name: str = Field(min_length=1)
    status: SystemCheckStatus
    message: str | None = None
    checked_at: str
    valid_until: str
