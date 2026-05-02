"""[SPEC-C-102] POST /preferences/writeback-suggestions.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-3 (writeback API).

Thin HTTP shim over :class:`StagePreferenceService.generate_writeback_suggestions`.
Request body carries a list of historical :class:`StagePreference` rows
and the current settings snapshot; the response lists one suggestion
per current-settings key, labelled ``keep | update | add_stage_override``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field

from src.backend.services.stage_preference_service import (
    StagePreferenceService,
)
from src.shared.schemas.stage_preference import StagePreference

router = APIRouter()


class WritebackSuggestionsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    project_id: str = Field(min_length=1)
    phase: str = Field(min_length=1)
    current_settings: Dict[str, Any] = Field(default_factory=dict)
    historical_preferences: List[StagePreference] = Field(default_factory=list)
    confidence: float = 0.7


class WritebackSuggestionItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    key: str
    current: Any
    historical: Any
    recommended_action: Literal["keep", "update", "add_stage_override"]
    proposed_action: Literal["auto_save", "ask_writeback"]


class WritebackSuggestionsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    suggestions: List[WritebackSuggestionItem]


@router.post(
    "/preferences/writeback-suggestions",
    response_model=WritebackSuggestionsResponse,
    summary="Generate preference writeback suggestions",
    description=(
        "Given current settings and historical stage preferences, "
        "return one suggestion per key labelled keep/update/add_stage_override "
        "(SPEC-C §C-BDD-3 step 2). Suggestions with confidence > 0.85 on "
        "update/add_stage_override are tagged proposed_action='auto_save'."
    ),
)
def post_writeback_suggestions(
    req: WritebackSuggestionsRequest,
) -> WritebackSuggestionsResponse:
    service = StagePreferenceService()
    suggestions = service.generate_writeback_suggestions(
        project_id=req.project_id,
        phase=req.phase,
        current_settings=req.current_settings,
        historical_preferences=req.historical_preferences,
        confidence=req.confidence,
    )
    return WritebackSuggestionsResponse(
        suggestions=[
            WritebackSuggestionItem(
                key=s.key,
                current=s.current,
                historical=s.historical,
                recommended_action=s.recommended_action,
                proposed_action=s.proposed_action,
            )
            for s in suggestions
        ]
    )


__all__ = [
    "WritebackSuggestionItem",
    "WritebackSuggestionsRequest",
    "WritebackSuggestionsResponse",
    "post_writeback_suggestions",
    "router",
]
