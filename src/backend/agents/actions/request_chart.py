"""[SPEC-C-101] request_chart action params (v3.16 C-BDD-2).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-2.

Idempotency: (SHA-256(user_intent)) — 5 min.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

# Constrained chart-type enum from SPEC-C §C-BDD-6 (ChartIntentEngine).
ChartType = Literal["line", "bar", "candlestick", "area", "scatter", "heatmap"]


class RequestChartParams(BaseModel):
    """Params for a user request to insert / render a chart."""

    model_config = ConfigDict(extra="forbid")

    user_intent: str = Field(min_length=1)
    chart_type: Optional[ChartType] = None
    entity: Optional[str] = None
    time_range: Optional[str] = None


__all__ = ["ChartType", "RequestChartParams"]
