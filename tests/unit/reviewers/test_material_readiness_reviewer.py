"""[SPEC-C-022] Unit tests for MaterialReadinessReviewer.

AC-5: Reviewer and Check must agree on the same input (verdict parity).
Also covers the ConsistencyError surface when the programmatic Check
and the Reviewer disagree (guard kept so any future divergence is loud
rather than silent).
"""

from __future__ import annotations

import pytest

from src.backend.reviewers.material_readiness_reviewer import (
    ConsistencyError,
    MaterialReadinessReviewer,
)
from src.backend.services.material_readiness_check import (
    MaterialReadinessCheck,
)
from src.shared.schemas.material_manifest import (
    MaterialEntry,
    MaterialManifest,
    MaterialSource,
    MaterialType,
    RequiredLevel,
    SourceKind,
    VerificationStatus,
)
from src.shared.schemas.shot_material_bindings import (
    ShotBinding,
    ShotMaterialBindings,
)


def _entry(
    material_id: str,
    shot_id: str,
    status: VerificationStatus = VerificationStatus.VERIFIED,
) -> MaterialEntry:
    return MaterialEntry(
        material_id=material_id,
        shot_id=shot_id,
        material_type=MaterialType.FACT,
        required=RequiredLevel.HARD,
        source=MaterialSource(kind=SourceKind.API, ref="ref"),
        verification_status=status,
        fetched_at="2026-04-24T00:00:00Z",
        rationale="test",
    )


class TestAC5ReviewerConsistentWithCheck:
    def test_pass_when_check_passes(self) -> None:
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[_entry("mat_500", "shot_01")],
        )
        bindings = ShotMaterialBindings(
            bindings=[
                ShotBinding(
                    shot_id="shot_01",
                    required_materials=["mat_500"],
                    optional_materials=[],
                )
            ]
        )

        check_result = MaterialReadinessCheck.check(
            manifest=manifest, bindings=bindings
        )
        report = MaterialReadinessReviewer.review(manifest=manifest, bindings=bindings)

        expected = "PASS" if check_result.ok else "FAIL"
        assert report.verdict == expected == "PASS"

    def test_fail_when_check_fails(self) -> None:
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[_entry("mat_501", "shot_01", status=VerificationStatus.PENDING)],
        )
        bindings = ShotMaterialBindings(
            bindings=[
                ShotBinding(
                    shot_id="shot_01",
                    required_materials=["mat_501"],
                    optional_materials=[],
                )
            ]
        )

        check_result = MaterialReadinessCheck.check(
            manifest=manifest, bindings=bindings
        )
        report = MaterialReadinessReviewer.review(manifest=manifest, bindings=bindings)

        expected = "PASS" if check_result.ok else "FAIL"
        assert report.verdict == expected == "FAIL"

    def test_consistency_error_on_verdict_mismatch(self) -> None:
        """Explicit guard: if a caller ever bypasses the reviewer delegation
        and hands it an inconsistent pair, assert_consistent raises.
        """
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[_entry("mat_502", "shot_01", status=VerificationStatus.PENDING)],
        )
        bindings = ShotMaterialBindings(
            bindings=[
                ShotBinding(
                    shot_id="shot_01",
                    required_materials=["mat_502"],
                    optional_materials=[],
                )
            ]
        )
        check_result = MaterialReadinessCheck.check(
            manifest=manifest, bindings=bindings
        )
        assert check_result.ok is False

        with pytest.raises(ConsistencyError):
            MaterialReadinessReviewer.assert_consistent(
                check_result=check_result, reviewer_verdict="PASS"
            )
