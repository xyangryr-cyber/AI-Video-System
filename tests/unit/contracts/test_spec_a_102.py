"""Tests for [SPEC-A-102] ProjectState.latest_reached_phase + PhaseDetailView contracts.

Delegates to the two aux modules listed in the task card's ``allowed_files``
(``test_project_state_v316.py`` + ``test_phase_detail_view_schema.py``).
Mirrors the A-100 / A-101 pattern so the task-card ``verification_commands``
(``pytest tests/unit/contracts/test_spec_a_102.py``) runs the real
AC-1..AC-4 assertions rather than the prior ``pytest.skip`` stubs.
"""

from __future__ import annotations

from tests.unit.contracts.test_phase_detail_view_schema import (
    TestAC2SevenSections as _TestAC2,
    TestAC4ReadOnlyDefault as _TestAC4,
    TestTsMirror as _TestTsMirror,
)
from tests.unit.contracts.test_project_state_v316 import (
    TestAC1MigrationBackfills as _TestAC1,
    TestAC3PhaseHistoryEntries as _TestAC3,
)


class TestAC1(_TestAC1):
    pass


class TestAC2(_TestAC2):
    pass


class TestAC3(_TestAC3):
    pass


class TestAC4(_TestAC4):
    pass


class TestTsMirror(_TestTsMirror):
    pass
