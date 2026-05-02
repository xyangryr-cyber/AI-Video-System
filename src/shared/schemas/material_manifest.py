"""[SPEC-A-015] MaterialManifest schema (Pydantic).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-3.

The P7A material manifest is the upstream artifact produced by
StoryboardAssetPlanner / MaterialFetcher / MaterialVerifier. Its
companion is `shot_material_bindings.json` — see
`src/shared/schemas/shot_material_bindings.py` for the binding-side
invariant. Keep this module in lockstep with
`schemas/material_manifest.schema.json` and
`src/shared/types/material_manifest.ts`.

Verification-status state machine (AC-5):

    pending -> verified | rejected | missing
    verified | rejected | missing -> pending  ONLY via supplement flow

`validate_verification_status_transition(old, new, *, via_supplement=False)`
is the single source of truth for the transition matrix; agents in the
P7A pipeline MUST route every status update through it.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

_MATERIAL_ID_RE = r"^mat_\d{3,}$"
_SHOT_ID_RE = r"^shot_\d{2,}$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MaterialType(str, Enum):
    CHART = "chart"
    FACT = "fact"
    NEWS = "news"
    FIGURE = "figure"
    ICON = "icon"
    IMAGE = "image"
    VIDEO = "video"
    QUOTE = "quote"


class RequiredLevel(str, Enum):
    HARD = "hard"
    SOFT = "soft"


class SourceKind(str, Enum):
    API = "api"
    URL = "url"
    INTERNAL = "internal"


class VerificationStatus(str, Enum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"
    MISSING = "missing"


class MaterialSource(_Strict):
    kind: SourceKind
    ref: str = Field(min_length=1)


class MaterialEntry(_Strict):
    material_id: str = Field(pattern=_MATERIAL_ID_RE)
    shot_id: str = Field(pattern=_SHOT_ID_RE)
    material_type: MaterialType
    required: RequiredLevel
    source: MaterialSource
    verification_status: VerificationStatus
    fetched_at: str = Field(min_length=1)
    verified_at: str | None = None
    rationale: str = Field(min_length=1)
    evidence_ref: str | None = None


class MaterialManifest(_Strict):
    project_id: str = Field(min_length=1)
    phase: Literal["7A"]
    materials: list[MaterialEntry]


_TERMINAL_STATES = {
    VerificationStatus.VERIFIED,
    VerificationStatus.REJECTED,
    VerificationStatus.MISSING,
}


def validate_verification_status_transition(
    old: VerificationStatus,
    new: VerificationStatus,
    *,
    via_supplement: bool = False,
) -> None:
    """AC-5 state-machine guard.

    Legal transitions:
      - any -> same (idempotent no-op)
      - pending -> {verified, rejected, missing}
      - {verified, rejected, missing} -> pending ONLY when `via_supplement=True`

    Every other transition raises ValueError. Non-enum inputs raise TypeError.
    """
    if not isinstance(old, VerificationStatus) or not isinstance(new, VerificationStatus):
        raise TypeError(
            "old/new must be VerificationStatus enum members; "
            f"got old={type(old).__name__}, new={type(new).__name__}"
        )

    if old == new:
        return

    if old == VerificationStatus.PENDING and new in _TERMINAL_STATES:
        return

    if old in _TERMINAL_STATES and new == VerificationStatus.PENDING:
        if via_supplement:
            return
        raise ValueError(
            f"illegal transition {old.value} -> {new.value} without "
            "explicit supplement flow (pass via_supplement=True)"
        )

    raise ValueError(f"illegal verification_status transition: {old.value} -> {new.value}")


__all__ = [
    "MaterialEntry",
    "MaterialManifest",
    "MaterialSource",
    "MaterialType",
    "RequiredLevel",
    "SourceKind",
    "VerificationStatus",
    "validate_verification_status_transition",
]
