"""[SPEC-C-102] StagePreferenceService: runtime injection + writeback suggestions.

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-3.

Two responsibilities:
1. ``inject_preferences`` -- at runtime stage X, surface only the
   preferences that ``STAGE_INJECTION_MATRIX`` permits for stage X
   (prevents a P5 pref from polluting P4).
2. ``generate_writeback_suggestions`` -- diff current settings against
   historical preferences and label each key
   ``keep | update | add_stage_override`` per SPEC-C §C-BDD-3 step 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from src.shared.constants.stage_injection_matrix import stage_accepts_key
from src.shared.schemas.stage_preference import Stage, StagePreference

RecommendedAction = Literal["keep", "update", "add_stage_override"]
ProposedAction = Literal["auto_save", "ask_writeback"]

AUTO_SAVE_THRESHOLD = 0.85


@dataclass(frozen=True)
class WritebackSuggestion:
    key: str
    current: Any
    historical: Any
    recommended_action: RecommendedAction
    proposed_action: ProposedAction = "ask_writeback"


class StagePreferenceService:
    """Stateless service -- no DB, no I/O. Pure transforms on inputs."""

    def inject_preferences(
        self,
        *,
        stage: Stage,
        available: list[StagePreference],
    ) -> list[StagePreference]:
        """Return the subset of ``available`` that is legal to inject at ``stage``.

        - Global / cross_project / project scope: always pass through.
        - Stage scope: must match ``stage`` AND key must be accepted by the
          STAGE_INJECTION_MATRIX row for that stage.
        """
        surfaced: list[StagePreference] = []
        for pref in available:
            if pref.scope == "stage":
                if pref.stage != stage:
                    continue
                if not stage_accepts_key(stage, pref.key):
                    continue
            surfaced.append(pref)
        return surfaced

    def generate_writeback_suggestions(
        self,
        *,
        project_id: str,
        phase: str,
        current_settings: dict[str, Any],
        historical_preferences: list[StagePreference],
        confidence: float = 0.7,
    ) -> list[WritebackSuggestion]:
        """Produce one suggestion per key in ``current_settings``.

        SPEC-C §C-BDD-3 step 2:
          values equal -> keep
          historical differs -> update
          no historical record -> add_stage_override
        Step 3: confidence > 0.85 on update/add_stage_override -> auto_save,
        otherwise ask_writeback.
        """
        by_key: dict[str, StagePreference] = {p.key: p for p in historical_preferences}
        out: list[WritebackSuggestion] = []
        for key, current_value in current_settings.items():
            historical_pref: StagePreference | None = by_key.get(key)
            if historical_pref is None:
                action: RecommendedAction = "add_stage_override"
                historical_value: Any = None
            elif historical_pref.value == current_value:
                action = "keep"
                historical_value = historical_pref.value
            else:
                action = "update"
                historical_value = historical_pref.value

            if action in ("update", "add_stage_override"):
                proposed: ProposedAction = (
                    "auto_save" if confidence > AUTO_SAVE_THRESHOLD else "ask_writeback"
                )
            else:
                proposed = "ask_writeback"

            out.append(
                WritebackSuggestion(
                    key=key,
                    current=current_value,
                    historical=historical_value,
                    recommended_action=action,
                    proposed_action=proposed,
                )
            )
        return out


__all__ = [
    "ProposedAction",
    "RecommendedAction",
    "StagePreferenceService",
    "WritebackSuggestion",
]
