"""Pydantic model for [SPEC-A-103] ChartStyleOverrides.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-4 (SPEC-0A.11).

All fields are optional — when unset, the downstream renderer falls
back to ``style_lock`` defaults (v3.15). ``line_color`` MUST belong to
``style_lock.color_palette``; that cross-reference check lives in the
P8 renderer, not in this schema (spec prose §A-BDD-4 note 2).

Mirrored in TypeScript by ``src/shared/types/chart_request.ts``.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ChartStyleOverrides(BaseModel):
    model_config = ConfigDict(extra="forbid")

    line_width: float | None = None
    line_color: str | None = None
    smooth: bool | None = None
    background_color: str | None = None
    grid_visible: bool | None = None
    show_source_label: bool | None = None
    animation_duration_ms: int | None = None


__all__ = ["ChartStyleOverrides"]
