"""Tests for [SPEC-A-104] task_ledger.type 扩展至 BDD 动作.

Delegates to the aux module listed in the task card ``allowed_files``
(``test_task_types_contract.py``). Mirrors the A-100 / A-101 / A-102 / A-103
pattern so the task-card ``verification_commands``
(``pytest tests/unit/contracts/test_spec_a_104.py -v``) runs the real
AC-1..AC-3 assertions rather than the prior ``pytest.skip`` stubs.
"""

from __future__ import annotations

from tests.unit.contracts.test_task_types_contract import (
    TestAC1TaskLedgerTypeEnumAppendsSix as _TestAC1,
    TestAC2FifteenWithIdempotencyKeysForNewSix as _TestAC2,
    TestAC3MigrationCheckConstraintRejectsUnknownType as _TestAC3,
)


class TestAC1(_TestAC1):
    pass


class TestAC2(_TestAC2):
    pass


class TestAC3(_TestAC3):
    pass
