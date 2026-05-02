"""[SPEC-C-101] save_stage_preference action params (v3.16 C-BDD-2).

Authority: docs/specs/SPEC-C-backend-core.md §C-BDD-2.

Idempotency: (scope, stage, key) — upsert (no TTL).
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Mirrors src/shared/schemas/stage_preference.py (SPEC-A-101).
Scope = Literal["global", "cross_project", "project", "stage"]
Stage = Literal[
    "P2_script",
    "P3_polish",
    "P4_tts",
    "P5_bgm",
    "P6_sfx",
    "P7_storyboard",
    "P8_keyframe",
    "P9_broll",
    "P10_roughcut",
    "P11_finalize",
]
PreferenceSource = Literal[
    "user_explicit",
    "extracted_from_revision",
    "extracted_from_confirmation",
]


class SaveStagePreferenceParams(BaseModel):
    """Params for a user writeback of a preference rule."""

    model_config = ConfigDict(extra="forbid")

    scope: Scope
    stage: Stage | None = None
    key: str = Field(min_length=1)
    value: str | int | float | bool
    source: PreferenceSource

    @model_validator(mode="after")
    def _stage_matches_scope(self) -> SaveStagePreferenceParams:
        if self.scope == "stage" and self.stage is None:
            raise ValueError("scope='stage' requires `stage` to be set")
        if self.scope != "stage" and self.stage is not None:
            raise ValueError(
                f"scope='{self.scope}' must not carry a `stage` value (got {self.stage!r})"
            )
        return self


__all__ = [
    "PreferenceSource",
    "SaveStagePreferenceParams",
    "Scope",
    "Stage",
]
