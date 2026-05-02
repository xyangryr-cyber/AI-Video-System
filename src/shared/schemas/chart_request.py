"""Pydantic models for [SPEC-A-103] ChartRequest.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-4 (SPEC-0A.11).

``ChartRequest`` captures the user's chart intent as it traverses the
7-state machine
``awaiting_clarification -> fetching -> awaiting_verification ->
awaiting_confirmation -> rendering -> completed`` (with ``failed`` as
a terminal branch from every non-terminal state). Runtime-only state:
written to ``task_ledger.params`` and NOT persisted to a dedicated
table (SPEC §A-BDD-4 storage note).

``fetched_data_ref`` points at a ``claim_id`` (SPEC-A-100) or data
snapshot once fetching completes — this is the "claim_refs" coupling
called out in the SPEC-A-103 task card scope.

Mirrored in TypeScript by ``src/shared/types/chart_request.ts``.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from src.shared.schemas.axis_spec import AxisSpec
from src.shared.schemas.chart_style_overrides import ChartStyleOverrides

ChartType = Literal[
    "line",
    "bar",
    "candlestick",
    "pie",
    "area",
    "scatter",
]

ChartRequestStatus = Literal[
    "awaiting_clarification",
    "fetching",
    "awaiting_verification",
    "awaiting_confirmation",
    "rendering",
    "completed",
    "failed",
]

TimeGranularity = Literal["day", "week", "month", "year"]


class TimeRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: str = Field(min_length=1)
    end: str = Field(min_length=1)
    granularity: TimeGranularity


class ChartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str = Field(min_length=1)
    user_intent: str = Field(min_length=1)
    chart_type: Optional[ChartType] = None
    entity: Optional[str] = None
    time_range: Optional[TimeRange] = None
    unit: Optional[str] = None
    comparison_targets: Optional[List[str]] = None
    status: ChartRequestStatus
    pending_clarifications: Optional[List[str]] = None
    fetched_data_ref: Optional[str] = None
    axis_spec: Optional[AxisSpec] = None
    style_overrides: Optional[ChartStyleOverrides] = None


__all__ = [
    "ChartRequest",
    "ChartRequestStatus",
    "ChartType",
    "TimeGranularity",
    "TimeRange",
]
