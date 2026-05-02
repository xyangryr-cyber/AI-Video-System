"""Pydantic models for [SPEC-A-101] StagePreference.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-2 (SPEC-0A.9).

`StagePreference` represents a single preference row with a scope
(``global`` / ``cross_project`` / ``project`` / ``stage``). Runtime
injection uses ``STAGE_INJECTION_MATRIX``
(src/shared/constants/stage_injection_matrix.py) to prevent a preference
from one phase leaking into another (e.g. P5 BGM parameters MUST NOT be
injected into P4 TTS).

The priority chain ``stage > project > cross_project > global`` is a
system invariant and is enforced here via ``resolve_preference``. The
BDD prose between cross_project and global mentions a legacy ``user``
tier; in v3.16 that tier is folded into ``cross_project`` (the v3.15
``user_preferences_md`` source).

Mirrors ``src/shared/types/stage_preference.ts`` and the SQL DDL in
``migrations/V003__create_stage_preferences.sql``.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

# Priority rank: lower number = higher priority.
_SCOPE_RANK = {"stage": 0, "project": 1, "cross_project": 2, "global": 3}


class StagePreference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    preference_id: str = Field(min_length=1)
    scope: Scope
    stage: Stage | None = None
    key: str = Field(min_length=1)
    value: str | int | float | bool
    source: PreferenceSource
    applies_to_artifacts: list[str] = Field(default_factory=list)
    evidence_segment_id: str | None = None
    created_at: str = Field(min_length=1)
    expires_at: str | None = None

    @model_validator(mode="after")
    def _stage_matches_scope(self) -> StagePreference:
        if self.scope == "stage" and self.stage is None:
            raise ValueError("scope='stage' requires `stage` to be set")
        if self.scope != "stage" and self.stage is not None:
            raise ValueError(
                f"scope='{self.scope}' must not carry a `stage` value "
                f"(got {self.stage!r}); cross-scope injection is forbidden"
            )
        return self


def resolve_preference(
    prefs: Iterable[StagePreference],
    *,
    key: str,
    stage: Stage | None = None,
    project_id: str | None = None,
) -> StagePreference | None:
    """Return the winning preference for ``key`` under priority chain.

    Order (highest → lowest): ``stage`` (matching ``stage``) >
    ``project`` > ``cross_project`` > ``global``. Preferences whose
    ``stage`` does not match the runtime stage are dropped (a P3 stage
    pref must NOT win for a P4 resolution — AC-4 edge case).
    """
    best: StagePreference | None = None
    best_rank = 1 << 30
    for p in prefs:
        if p.key != key:
            continue
        if p.scope == "stage" and p.stage != stage:
            continue
        rank = _SCOPE_RANK[p.scope]
        if rank < best_rank:
            best, best_rank = p, rank
    return best


__all__ = [
    "PreferenceSource",
    "Scope",
    "Stage",
    "StagePreference",
    "resolve_preference",
]
