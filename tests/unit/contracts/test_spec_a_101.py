"""Tests for [SPEC-A-101] StagePreference + STAGE_INJECTION_MATRIX.

Delegates to the aux module ``test_stage_preference.py`` listed in the
task card's ``allowed_files``. This file mirrors the A-100 pattern so
``pytest tests/unit/contracts/test_spec_a_101.py`` (the task-card
``verification_commands``) runs the real AC-1..AC-5 assertions.
"""

from __future__ import annotations

from tests.unit.contracts.test_stage_preference import (
    TestAC1StagePreferenceSchema as _TestAC1,
    TestAC2InjectionMatrix as _TestAC2,
    TestAC3MigrationCreatesStagePreferences as _TestAC3,
    TestAC4PriorityChain as _TestAC4,
    TestAC5CrossStageInjectionIsolation as _TestAC5,
    TestTsMirror as _TestTs,
)


class TestAC1(_TestAC1):
    pass


class TestAC2(_TestAC2):
    pass


class TestAC3(_TestAC3):
    pass


class TestAC4(_TestAC4):
    pass


class TestAC5(_TestAC5):
    pass


class TestTs(_TestTs):
    pass
