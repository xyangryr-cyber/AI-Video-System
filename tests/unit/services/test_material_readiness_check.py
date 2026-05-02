"""[SPEC-C-022] Unit tests for MaterialReadinessCheck service.

Covers:
  * AC-1 — all verified -> ok=True, blocked_shots=[].
  * AC-2 — 1 hard required = PENDING/REJECTED -> ok=False + error_code
           mapping (pending/rejected -> material_unverified,
           missing -> material_missing).
  * AC-3 — 1 soft required = unverified -> ok=True, WARN logged.
  * AC-6 — bindings.required_materials references material_id absent
           from manifest -> ok=False, error_code=material_missing.
  * AC-7 — Check runtime < 200ms for 100 shots.
"""

from __future__ import annotations

import logging
import time

import pytest

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
    *,
    material_id: str,
    shot_id: str,
    status: VerificationStatus = VerificationStatus.VERIFIED,
    required: RequiredLevel = RequiredLevel.HARD,
) -> MaterialEntry:
    return MaterialEntry(
        material_id=material_id,
        shot_id=shot_id,
        material_type=MaterialType.FACT,
        required=required,
        source=MaterialSource(kind=SourceKind.API, ref="ref/" + material_id),
        verification_status=status,
        fetched_at="2026-04-24T00:00:00Z",
        rationale="test",
    )


class TestAC1AllVerifiedReturnsOk:
    def test_all_verified_returns_ok(self) -> None:
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[
                _entry(material_id="mat_001", shot_id="shot_01"),
                _entry(material_id="mat_002", shot_id="shot_02"),
            ],
        )
        bindings = ShotMaterialBindings(
            bindings=[
                ShotBinding(
                    shot_id="shot_01",
                    required_materials=["mat_001"],
                    optional_materials=[],
                ),
                ShotBinding(
                    shot_id="shot_02",
                    required_materials=["mat_002"],
                    optional_materials=[],
                ),
            ]
        )

        result = MaterialReadinessCheck.check(manifest=manifest, bindings=bindings)

        assert result.ok is True
        assert result.blocked_shots == []


class TestAC2HardUnverifiedBlocksWithErrorCode:
    def test_hard_pending_yields_material_unverified(self) -> None:
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[
                _entry(
                    material_id="mat_100",
                    shot_id="shot_01",
                    status=VerificationStatus.PENDING,
                ),
            ],
        )
        bindings = ShotMaterialBindings(
            bindings=[
                ShotBinding(
                    shot_id="shot_01",
                    required_materials=["mat_100"],
                    optional_materials=[],
                ),
            ]
        )

        result = MaterialReadinessCheck.check(manifest=manifest, bindings=bindings)

        assert result.ok is False
        assert len(result.blocked_shots) == 1
        bs = result.blocked_shots[0]
        assert bs.shot_id == "shot_01"
        assert bs.error_code == "material_unverified"
        assert bs.blocking_material_ids == ["mat_100"]

    def test_hard_rejected_yields_material_unverified(self) -> None:
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[
                _entry(
                    material_id="mat_101",
                    shot_id="shot_01",
                    status=VerificationStatus.REJECTED,
                ),
            ],
        )
        bindings = ShotMaterialBindings(
            bindings=[
                ShotBinding(
                    shot_id="shot_01",
                    required_materials=["mat_101"],
                    optional_materials=[],
                ),
            ]
        )

        result = MaterialReadinessCheck.check(manifest=manifest, bindings=bindings)

        assert result.ok is False
        assert result.blocked_shots[0].error_code == "material_unverified"
        assert result.blocked_shots[0].blocking_material_ids == ["mat_101"]

    def test_hard_missing_yields_material_missing(self) -> None:
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[
                _entry(
                    material_id="mat_102",
                    shot_id="shot_01",
                    status=VerificationStatus.MISSING,
                ),
            ],
        )
        bindings = ShotMaterialBindings(
            bindings=[
                ShotBinding(
                    shot_id="shot_01",
                    required_materials=["mat_102"],
                    optional_materials=[],
                ),
            ]
        )

        result = MaterialReadinessCheck.check(manifest=manifest, bindings=bindings)

        assert result.ok is False
        assert result.blocked_shots[0].error_code == "material_missing"
        assert result.blocked_shots[0].blocking_material_ids == ["mat_102"]


class TestAC3SoftUnverifiedWarnsNotBlocks:
    def test_soft_unverified_ok_with_warn_log(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[
                _entry(material_id="mat_200", shot_id="shot_01"),
                _entry(
                    material_id="mat_201",
                    shot_id="shot_01",
                    status=VerificationStatus.PENDING,
                    required=RequiredLevel.SOFT,
                ),
            ],
        )
        bindings = ShotMaterialBindings(
            bindings=[
                ShotBinding(
                    shot_id="shot_01",
                    required_materials=["mat_200"],
                    optional_materials=["mat_201"],
                ),
            ]
        )

        with caplog.at_level(logging.WARNING):
            result = MaterialReadinessCheck.check(manifest=manifest, bindings=bindings)

        assert result.ok is True
        assert result.blocked_shots == []
        warn_msgs = [r for r in caplog.records if r.levelno == logging.WARNING]
        assert warn_msgs, "expected WARN log for soft-unverified material"
        assert any("mat_201" in r.getMessage() for r in warn_msgs)


class TestAC6CountMismatchYieldsMaterialMissing:
    def test_required_binding_refers_to_unknown_material(self) -> None:
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[
                _entry(material_id="mat_300", shot_id="shot_01"),
            ],
        )
        bindings = ShotMaterialBindings(
            bindings=[
                ShotBinding(
                    shot_id="shot_01",
                    required_materials=["mat_300", "mat_999"],
                    optional_materials=[],
                ),
            ]
        )

        result = MaterialReadinessCheck.check(manifest=manifest, bindings=bindings)

        assert result.ok is False
        assert len(result.blocked_shots) == 1
        bs = result.blocked_shots[0]
        assert bs.error_code == "material_missing"
        assert "mat_999" in bs.blocking_material_ids


class TestAC7CheckPerfUnder200ms:
    def test_check_runtime_under_200ms_for_100_shots(self) -> None:
        materials: list[MaterialEntry] = []
        bindings_list: list[ShotBinding] = []
        for i in range(100):
            shot_id = f"shot_{i:02d}" if i < 100 else f"shot_{i}"
            # material_id pattern requires 3+ digits
            mid = f"mat_{400 + i:03d}"
            materials.append(_entry(material_id=mid, shot_id=shot_id))
            bindings_list.append(
                ShotBinding(
                    shot_id=shot_id,
                    required_materials=[mid],
                    optional_materials=[],
                )
            )
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=materials,
        )
        bindings = ShotMaterialBindings(bindings=bindings_list)

        t0 = time.perf_counter()
        result = MaterialReadinessCheck.check(manifest=manifest, bindings=bindings)
        elapsed_ms = (time.perf_counter() - t0) * 1000.0

        assert result.ok is True
        assert elapsed_ms < 200.0, f"Check took {elapsed_ms:.2f}ms, budget 200ms"
