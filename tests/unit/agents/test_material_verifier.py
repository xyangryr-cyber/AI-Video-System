"""[SPEC-C-021] MaterialVerifier unit tests (AC-3).

Three terminal states tested in isolation:
  * verified — L1 file-exists + L2 FactChecker pass
  * missing  — L1 file-missing (even with fetched_at set)
  * rejected — L1 pass + L2 FactChecker fail

All L1+L2 transitions go through
:func:`validate_verification_status_transition` from A-015.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.backend.agents.material_verifier import MaterialVerifier
from src.shared.schemas.material_manifest import (
    MaterialEntry,
    MaterialSource,
    MaterialType,
    RequiredLevel,
    SourceKind,
    VerificationStatus,
)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    root = tmp_path / "proj_c021"
    (root / "phase_7a" / "verified_materials").mkdir(parents=True, exist_ok=True)
    return root


def _fetched_entry(material_id: str) -> MaterialEntry:
    return MaterialEntry(
        material_id=material_id,
        shot_id="shot_01",
        material_type=MaterialType.FACT,
        required=RequiredLevel.HARD,
        source=MaterialSource(kind=SourceKind.API, ref="r"),
        verification_status=VerificationStatus.PENDING,
        fetched_at="2026-04-24T00:00:00Z",
        rationale="for tests",
    )


class PassingFact:
    def check(self, entry: MaterialEntry, path: Path) -> tuple[bool, str]:
        return True, ""


class RejectingFact:
    def check(self, entry: MaterialEntry, path: Path) -> tuple[bool, str]:
        return False, "metric mismatch"


class TestAC3VerifierStates:
    def test_verify_verified(self, project_root: Path) -> None:
        out = project_root / "phase_7a" / "verified_materials" / "mat_010.json"
        out.write_bytes(b'{"foo": 1}')
        entry = _fetched_entry("mat_010")

        v = MaterialVerifier(project_root=project_root, fact_checker=PassingFact())
        updated = v.verify(entry)
        assert updated.verification_status == VerificationStatus.VERIFIED
        assert updated.verified_at

    def test_verify_missing(self, project_root: Path) -> None:
        # No file staged under verified_materials/ => L1 missing.
        entry = _fetched_entry("mat_011")
        v = MaterialVerifier(project_root=project_root)
        updated = v.verify(entry)
        assert updated.verification_status == VerificationStatus.MISSING

    def test_verify_rejected(self, project_root: Path) -> None:
        out = project_root / "phase_7a" / "verified_materials" / "mat_012.json"
        out.write_bytes(b'{"bad": true}')
        entry = _fetched_entry("mat_012")

        v = MaterialVerifier(project_root=project_root, fact_checker=RejectingFact())
        updated = v.verify(entry)
        assert updated.verification_status == VerificationStatus.REJECTED
