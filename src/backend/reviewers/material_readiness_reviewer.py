"""[SPEC-C-022] MaterialReadinessReviewer — Gate 7A reviewer entry.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-7.

Thin wrapper around
:class:`~src.backend.services.material_readiness_check.MaterialReadinessCheck`
so the Reviewer surface (Gate 7A) shares a single source of truth with
the programmatic P8 pre-flight gate: identical inputs MUST yield
identical verdicts (AC-5). If a caller ever hands an out-of-band verdict
to :meth:`assert_consistent`, :class:`ConsistencyError` surfaces the
divergence loudly rather than letting the mismatch slip through.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from src.backend.services.material_readiness_check import (
    MaterialReadinessCheck,
    ReadinessResult,
)
from src.shared.schemas.material_manifest import MaterialManifest
from src.shared.schemas.shot_material_bindings import ShotMaterialBindings

Verdict = Literal["PASS", "FAIL"]


class ReviewVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    check_name: str
    verdict: Verdict
    reason: str
    metrics: dict[str, Any] = Field(default_factory=dict)


class ReviewReport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    verdict: Verdict
    checks: list[ReviewVerdict]


class ConsistencyError(Exception):
    """Raised when Reviewer and Check disagree on a given input."""


class MaterialReadinessReviewer:
    """Gate 7A reviewer front-end; delegates to MaterialReadinessCheck."""

    __slots__ = ()

    @staticmethod
    def review(
        *,
        manifest: MaterialManifest,
        bindings: ShotMaterialBindings,
    ) -> ReviewReport:
        result = MaterialReadinessCheck.check(manifest=manifest, bindings=bindings)
        verdict: Verdict = "PASS" if result.ok else "FAIL"
        reason = (
            "all HARD-required materials verified"
            if result.ok
            else f"{len(result.blocked_shots)} shot(s) blocked"
        )
        return ReviewReport(
            verdict=verdict,
            checks=[
                ReviewVerdict(
                    check_name="material_readiness",
                    verdict=verdict,
                    reason=reason,
                    metrics={"blocked_shots": [bs.model_dump() for bs in result.blocked_shots]},
                )
            ],
        )

    @staticmethod
    def assert_consistent(
        *,
        check_result: ReadinessResult,
        reviewer_verdict: Verdict,
    ) -> None:
        """Raise ``ConsistencyError`` when the two verdicts disagree.

        Kept as an explicit guard so divergence between the programmatic
        Check and the Reviewer front-end is loud rather than silent.
        """
        expected: Verdict = "PASS" if check_result.ok else "FAIL"
        if reviewer_verdict != expected:
            raise ConsistencyError(
                "MaterialReadinessReviewer verdict "
                f"{reviewer_verdict!r} disagrees with Check verdict "
                f"{expected!r}"
            )


__all__ = [
    "ConsistencyError",
    "MaterialReadinessReviewer",
    "ReviewReport",
    "ReviewVerdict",
    "Verdict",
]
