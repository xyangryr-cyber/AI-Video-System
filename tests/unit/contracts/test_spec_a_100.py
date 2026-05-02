"""Tests for [SPEC-A-100] Claim / VerificationRecord unified data model.

Delegates to the two aux test modules listed in the task card
`allowed_files` (test_claim_schema.py + test_claim_migration.py). This
file mirrors the A-001 / A-007 pattern so the task-card
`verification_commands` (`pytest tests/unit/contracts/test_spec_a_100.py`)
runs the real AC-1..AC-5 assertions, not the prior `pytest.skip` stubs.
"""

from __future__ import annotations

from tests.unit.contracts.test_claim_migration import (
    TestAC3MigrationCreatesTables as _TestAC3MigrationCreatesTables,
    TestAC4LegacyDataPointIdPreserved as _TestAC4LegacyDataPointIdPreserved,
)
from tests.unit.contracts.test_claim_schema import (
    TestAC1ClaimPydantic as _TestAC1ClaimPydantic,
    TestAC2VerificationRecordPydantic as _TestAC2VerificationRecordPydantic,
    TestAC5TsInterfaceMatchesPydantic as _TestAC5TsInterfaceMatchesPydantic,
)


class TestAC1(_TestAC1ClaimPydantic):
    pass


class TestAC2(_TestAC2VerificationRecordPydantic):
    pass


class TestAC3(_TestAC3MigrationCreatesTables):
    pass


class TestAC4(_TestAC4LegacyDataPointIdPreserved):
    pass


class TestAC5(_TestAC5TsInterfaceMatchesPydantic):
    pass
