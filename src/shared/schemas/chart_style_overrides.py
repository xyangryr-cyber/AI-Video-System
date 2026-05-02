"""Pydantic model for [SPEC-A-103] ChartStyleOverrides.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-4 (SPEC-0A.11).

All fields are optional — when unset, the downstream renderer falls
back to ``style_lock`` defaults (v3.15). ``line_color`` MUST belong to
``style_lock.color_palette``; that cross-reference check lives in the
P8 renderer, not in this schema (spec prose §A-BDD-4 note 2).

Mirrored in TypeScript by ``src/shared/types/chart_request.ts``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict


class ChartStyleOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_width: Optional[float] = None
    line_color: Optional[str] = None
    smooth: Optional[bool] = None
    background_color: Optional[str] = None
    grid_visible: Optional[bool] = None
    show_source_label: Optional[bool] = None
    animation_duration_ms: Optional[int] = None


__all__ = ["ChartStyleOverrides"]
