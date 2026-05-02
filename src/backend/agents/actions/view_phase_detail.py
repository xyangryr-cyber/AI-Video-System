"""[SPEC-C-101] view_phase_detail action params (v3.16 C-BDD-2).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-2.

Idempotency: none — read-only navigation, never persisted.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

Phase = Literal[
    "P0",
    "P1",
    "P2",
    "P3",
    "P4",
    "P5",
    "P6",
    "P7",
    "P7A",
    "P8",
    "P9",
    "P10",
    "P11",
]


class ViewPhaseDetailParams(BaseModel):
    """Params for a user navigation into a phase detail panel."""

    model_config = ConfigDict(extra="forbid")

    phase: Phase


__all__ = ["Phase", "ViewPhaseDetailParams"]
