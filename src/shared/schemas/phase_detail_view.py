"""Pydantic models for [SPEC-A-102] PhaseDetailView (SPEC-0A.10).

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-3.

`PhaseDetailView` is the payload for ``GET /projects/{id}/phases/{phase}/detail``.
It aggregates the 7 analytical blocks the BDD feature ``项目列表与阶段回看``
requires: artifacts / reviewer_results / gate_result / claim_snapshot /
preference_snapshot / diff_with_previous_version / operation_history.

The ``read_only`` flag is the locking contract: historical phases
(``phase < current_phase``) are read-only by default; the current
editable phase (``phase == current_phase``) must carry ``read_only=False``.
Flipping a historical phase to editable requires an explicit
``POST /projects/{id}/phases/{phase}/revert`` (per spec), so the schema
rejects the mixed states at validation time.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

PhaseDetailStatus = Literal["not_started", "in_progress", "completed", "invalidated"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PhaseDetailView(_Strict):
    """Full snapshot for one phase, served to the frontend phase-detail UI."""

    project_id: str = Field(min_length=1)
    phase: int = Field(ge=0, le=11)
    status: PhaseDetailStatus

    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    reviewer_results: List[Dict[str, Any]] = Field(default_factory=list)
    gate_result: Optional[Dict[str, Any]] = None
    claim_snapshot: List[Dict[str, Any]] = Field(default_factory=list)
    preference_snapshot: List[Dict[str, Any]] = Field(default_factory=list)
    diff_with_previous_version: Optional[Dict[str, Any]] = None
    operation_history: List[Dict[str, Any]] = Field(default_factory=list)

    read_only: bool = True
    current_phase: int = Field(ge=0, le=11)

    @model_validator(mode="after")
    def _read_only_matches_history(self) -> "PhaseDetailView":
        is_current = self.phase == self.current_phase
        if is_current and self.read_only:
            raise ValueError(
                "phase == current_phase must carry read_only=False "
                "(current editable phase cannot be locked)"
            )
        if not is_current and not self.read_only:
            raise ValueError(
                "historical phase (phase != current_phase) must carry "
                "read_only=True; unlock requires POST /phases/{phase}/revert"
            )
        return self


__all__ = ["PhaseDetailStatus", "PhaseDetailView"]
