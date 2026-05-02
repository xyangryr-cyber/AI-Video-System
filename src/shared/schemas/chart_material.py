"""[SPEC-A-016] ChartMaterial schema (Pydantic) with axis_spec sub-schema.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-4.

ChartMaterial is the P7A exit / P8 entry contract: a "fetched data +
generated axis" artifact produced by StoryboardAssetPlanner /
FinancialDataService and consumed by the P8 KeyframeRenderAgent (chart
templates).

Relationship with the v3.16 ChartRequest (user-intent layer, defined in
docs/specs/SPEC-A-contracts.md §A-BDD-4 / SPEC-0A.11): the two are
1:1 and linked by derivation rule

    request_id (^req_\\d{3,}$)  <-->  chart_id (^chart_\\d{3,}$)
    chart_id := "chart_" + numeric_suffix(request_id)

Use `derive_chart_id_from_request_id` / `derive_request_id_from_chart_id`
as the single source of truth for this mapping. ChartRequest itself is
NOT redefined here — agents holding a ChartRequest instance compute the
ChartMaterial.chart_id via the helper.

Cross-field invariants that JSON Schema cannot express are enforced in
this module:
- `axis_spec.y_axis.min < axis_spec.y_axis.max` (model_validator)
- `chart_spec.kind` <-> `axis_spec.x_axis.type` L1 consistency (surfaced
  as `validate_chart_axis_consistency`, raising
  `ChartAxisConsistencyError`).

Keep in lockstep with `schemas/chart_material.schema.json` and
`src/shared/types/chart_material.ts`.
"""

from __future__ import annotations

import re
from datetime import date, timedelta
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_CHART_ID_RE = r"^chart_\d{3,}$"
_SHOT_ID_RE = r"^shot_\d{2,}$"
_REQUEST_ID_RE = r"^req_\d{3,}$"
_DATE_RE = r"^\d{4}-\d{2}-\d{2}$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Granularity(str, Enum):
    DAY = "day"
    WEEK = "week"
    MONTH = "month"


class ChartKind(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"


class XAxisType(str, Enum):
    TIME = "time"
    CATEGORY = "category"
    VALUE = "value"


class ScaleMode(str, Enum):
    LINEAR = "linear"
    LOG = "log"


class DateRange(_Strict):
    start: str = Field(pattern=_DATE_RE)
    end: str = Field(pattern=_DATE_RE)


class ChartSource(_Strict):
    provider: str = Field(min_length=1)
    symbol: str = Field(min_length=1)


class ChartSpec(_Strict):
    kind: ChartKind
    series: list[Any] = Field(min_length=1)


class XAxis(_Strict):
    type: XAxisType
    labels: list[Any]
    range: list[Any] = Field(min_length=2, max_length=2)


class YAxis(_Strict):
    unit: str
    min: float
    max: float
    scale_mode: ScaleMode


class AxisSpec(_Strict):
    x_axis: XAxis
    y_axis: YAxis


class ChartMaterial(_Strict):
    chart_id: str = Field(pattern=_CHART_ID_RE)
    shot_id: str = Field(pattern=_SHOT_ID_RE)
    metric_name: str = Field(min_length=1)
    date_range: DateRange
    granularity: Granularity
    source: ChartSource
    verification_status: Literal["verified"]
    chart_spec: ChartSpec
    axis_spec: AxisSpec

    @model_validator(mode="after")
    def _y_axis_min_lt_max(self) -> ChartMaterial:
        y = self.axis_spec.y_axis
        if not (y.min < y.max):
            raise ValueError(
                f"axis_spec.y_axis.min ({y.min}) must be strictly less than max ({y.max})"
            )
        return self


class ChartAxisConsistencyError(ValueError):
    """Raised by the L1 check when chart_spec.kind is inconsistent with
    axis_spec.x_axis.type (see AC-6)."""


def validate_chart_axis_consistency(material: ChartMaterial) -> None:
    """L1 consistency check between chart kind and x-axis type.

    Rules:
      - `line`  -> x_axis.type MUST be `time` or `value` (category forbidden)
      - `bar`   -> x_axis.type MAY be `category`, `time`, or `value`
      - `pie`   -> x_axis.type MUST be `category` (time/value forbidden)

    The check is loud: raises `ChartAxisConsistencyError` on violation.
    """
    kind = material.chart_spec.kind
    x_type = material.axis_spec.x_axis.type

    legal: dict[ChartKind, set[XAxisType]] = {
        ChartKind.LINE: {XAxisType.TIME, XAxisType.VALUE},
        ChartKind.BAR: {XAxisType.CATEGORY, XAxisType.TIME, XAxisType.VALUE},
        ChartKind.PIE: {XAxisType.CATEGORY},
    }
    if x_type not in legal[kind]:
        raise ChartAxisConsistencyError(
            f"chart_spec.kind={kind.value} is inconsistent with "
            f"axis_spec.x_axis.type={x_type.value}; legal x_axis.type for "
            f"kind={kind.value} is "
            f"{{{', '.join(sorted(t.value for t in legal[kind]))}}}"
        )


def derive_chart_id_from_request_id(request_id: str) -> str:
    """`chart_id = "chart_" + numeric_suffix(request_id)`.

    Canonical 1:1 mapping between `ChartRequest.request_id` and
    `ChartMaterial.chart_id`. Raises ValueError on malformed input.
    """
    m = re.match(_REQUEST_ID_RE, request_id)
    if not m:
        raise ValueError(f"request_id must match {_REQUEST_ID_RE}, got {request_id!r}")
    return "chart_" + request_id[len("req_") :]


def derive_request_id_from_chart_id(chart_id: str) -> str:
    """Inverse of `derive_chart_id_from_request_id`."""
    m = re.match(_CHART_ID_RE, chart_id)
    if not m:
        raise ValueError(f"chart_id must match {_CHART_ID_RE}, got {chart_id!r}")
    return "req_" + chart_id[len("chart_") :]


def build_axis_x_labels(start: str, end: str, granularity: str | Granularity) -> list[str]:
    """Emit the canonical x_axis labels for a given date_range + granularity.

    AC-4 invariant (tolerance +/-1):
      - day   -> one label per calendar day in [start, end]
      - week  -> one label per 7-day step from start, inclusive of the
                 tail partial week
      - month -> one label per calendar month boundary in [start, end]

    Labels are ISO-8601 `YYYY-MM-DD` strings. Used by generators and
    tests to verify count-matching before the ChartMaterial is sealed.
    """
    g = Granularity(granularity) if not isinstance(granularity, Granularity) else granularity
    s = date.fromisoformat(start)
    e = date.fromisoformat(end)
    if e < s:
        raise ValueError(f"end {end} must be >= start {start}")
    labels: list[str] = []
    if g is Granularity.DAY:
        cur = s
        while cur <= e:
            labels.append(cur.isoformat())
            cur += timedelta(days=1)
    elif g is Granularity.WEEK:
        cur = s
        while cur <= e:
            labels.append(cur.isoformat())
            cur += timedelta(days=7)
    else:  # MONTH
        y, m = s.year, s.month
        while (y, m) <= (e.year, e.month):
            labels.append(date(y, m, 1).isoformat())
            m += 1
            if m > 12:
                m = 1
                y += 1
    return labels


__all__ = [
    "AxisSpec",
    "ChartAxisConsistencyError",
    "ChartKind",
    "ChartMaterial",
    "ChartSource",
    "ChartSpec",
    "DateRange",
    "Granularity",
    "ScaleMode",
    "XAxis",
    "XAxisType",
    "YAxis",
    "build_axis_x_labels",
    "derive_chart_id_from_request_id",
    "derive_request_id_from_chart_id",
    "validate_chart_axis_consistency",
]
