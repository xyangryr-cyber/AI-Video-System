"""Pydantic models for [SPEC-A-103] AxisSpec.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-4 (SPEC-0A.11).

``AxisSpec`` carries the explicit axis configuration that backs a
``ChartRequest`` once the user has clarified intent and data has been
fetched. Per SPEC, the y-axis MUST declare a ``zero_based`` boolean so
downstream renderers cannot silently pick their own baseline; the
x-axis deliberately does NOT carry ``zero_based`` because time/category
axes have no equivalent concept.

Mirrored in TypeScript by ``src/shared/types/chart_request.ts``.
"""

from __future__ import annotations

from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, StrictBool

XAxisType = Literal["time", "category", "value"]
YAxisType = Literal["value", "log"]


class XAxisSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: XAxisType
    min: Optional[Any] = None
    max: Optional[Any] = None
    tick_format: Optional[str] = None
    label: str = Field(min_length=1)


class YAxisSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: YAxisType
    min: Optional[float] = None
    max: Optional[float] = None
    zero_based: StrictBool
    unit: str
    label: str = Field(min_length=1)


class AxisSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    x_axis: XAxisSpec
    y_axis: YAxisSpec


__all__ = [
    "AxisSpec",
    "XAxisSpec",
    "YAxisSpec",
    "XAxisType",
    "YAxisType",
]
