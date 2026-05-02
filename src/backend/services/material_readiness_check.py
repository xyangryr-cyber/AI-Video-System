"""[SPEC-C-022] MaterialReadinessCheck — P8 pre-flight programmatic gate.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-7.

Before the async P8 render task starts, the WorkflowEngine (via
``src/backend/engine/p8_starter.py``) invokes this Check against the
phase_7a artifacts:

  * ``MaterialManifest`` (A-015) — the verification ledger.
  * ``ShotMaterialBindings`` (A-015) — per-shot HARD (``required_materials``)
    and SOFT (``optional_materials``) dependencies.

Returns :class:`ReadinessResult` whose ``ok`` is True iff every HARD-
required material_id referenced by a shot binding exists in the manifest
and has ``verification_status == VERIFIED``. Otherwise ``ok=False`` and
``blocked_shots`` enumerates each failing shot with an ``error_code``:

  * ``material_missing``    — referenced material_id is absent from the
                              manifest, or present with status=MISSING.
  * ``material_unverified`` — present with status=PENDING or REJECTED.

SOFT (``optional_materials``) failures are logged at WARN level but
never populate ``blocked_shots`` — AC-3 allows P8 to proceed.

Design: stateless class with a single ``@staticmethod`` entry point.
Keeps the Check trivially composable with
:class:`~src.backend.reviewers.material_readiness_reviewer.MaterialReadinessReviewer`
(AC-5 verdict parity) and keeps runtime at dict-lookup cost (AC-7).
"""

from __future__ import annotations

import logging
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from src.shared.schemas.material_manifest import (
    MaterialEntry,
    MaterialManifest,
    VerificationStatus,
)
from src.shared.schemas.shot_material_bindings import (
    ShotBinding,
    ShotMaterialBindings,
)

_LOG = logging.getLogger(__name__)

ErrorCode = Literal["material_missing", "material_unverified"]


class BlockedShot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shot_id: str
    error_code: ErrorCode
    blocking_material_ids: list[str] = Field(min_length=1)


class ReadinessResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ok: bool
    blocked_shots: list[BlockedShot]


def _classify(entry: MaterialEntry | None) -> ErrorCode | None:
    """Return the error_code for a single material lookup, or None when OK.

    Missing from manifest or terminal MISSING both map to
    ``material_missing``; PENDING / REJECTED map to
    ``material_unverified``; VERIFIED returns ``None`` (not blocking).
    """
    if entry is None:
        return "material_missing"
    status = entry.verification_status
    if status == VerificationStatus.VERIFIED:
        return None
    if status == VerificationStatus.MISSING:
        return "material_missing"
    # PENDING or REJECTED
    return "material_unverified"


class MaterialReadinessCheck:
    """Stateless P8 pre-flight gate (Gate 7A entry)."""

    __slots__ = ()

    @staticmethod
    def check(
        *,
        manifest: MaterialManifest,
        bindings: ShotMaterialBindings,
    ) -> ReadinessResult:
        by_id: dict[str, MaterialEntry] = {m.material_id: m for m in manifest.materials}

        blocked: list[BlockedShot] = []
        for binding in bindings.bindings:
            blocker = _evaluate_hard(binding, by_id)
            if blocker is not None:
                blocked.append(blocker)
            _warn_soft(binding, by_id)

        return ReadinessResult(ok=not blocked, blocked_shots=blocked)


def _evaluate_hard(
    binding: ShotBinding,
    by_id: dict[str, MaterialEntry],
) -> BlockedShot | None:
    missing_ids: list[str] = []
    unverified_ids: list[str] = []
    for mid in binding.required_materials:
        code = _classify(by_id.get(mid))
        if code == "material_missing":
            missing_ids.append(mid)
        elif code == "material_unverified":
            unverified_ids.append(mid)

    if not missing_ids and not unverified_ids:
        return None

    # Missing dominates unverified: when any required material_id is
    # absent / MISSING, the shot's blocker is material_missing and we
    # surface the missing ids first (the unverified ones may still be
    # visible in the blocking list for operator context).
    if missing_ids:
        return BlockedShot(
            shot_id=binding.shot_id,
            error_code="material_missing",
            blocking_material_ids=missing_ids + unverified_ids,
        )
    return BlockedShot(
        shot_id=binding.shot_id,
        error_code="material_unverified",
        blocking_material_ids=unverified_ids,
    )


def _warn_soft(
    binding: ShotBinding,
    by_id: dict[str, MaterialEntry],
) -> None:
    for mid in binding.optional_materials:
        code = _classify(by_id.get(mid))
        if code is None:
            continue
        _LOG.warning(
            "soft material %s for shot %s is %s; P8 proceeds",
            mid,
            binding.shot_id,
            code,
        )


__all__ = [
    "BlockedShot",
    "ErrorCode",
    "MaterialReadinessCheck",
    "ReadinessResult",
]
