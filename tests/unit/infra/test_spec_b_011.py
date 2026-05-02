"""Tests for [SPEC-B-011] Production Rollout/Rollback Scripts (aggregator-shim).

Delegates to the real test module listed in the task card's ``allowed_files``:
- tests/unit/infra/test_rollback_scripts.py (AC-1..AC-5)

Re-exports via class-inheritance so the task-card verification command
``pytest tests/unit/infra/test_spec_b_011.py`` runs the real assertions
(A-100..A-105 / B-015 / B-016 / B-007 / B-008 / B-010 precedent).
"""

from __future__ import annotations

from tests.unit.infra.test_rollback_scripts import (
    TestAC1ComposeRollbackDryRun as _TestAC1,
    TestAC2SchemaRollbackDryRun as _TestAC2,
    TestAC3WorkerRecoveryDryRun as _TestAC3,
    TestAC4HealthCheckInScripts as _TestAC4,
    TestAC5DryRunNoSideEffects as _TestAC5,
)


class TestAC1ComposeRollbackDryRun(_TestAC1):
    pass


class TestAC2SchemaRollbackDryRun(_TestAC2):
    pass


class TestAC3WorkerRecoveryDryRun(_TestAC3):
    pass


class TestAC4HealthCheckInScripts(_TestAC4):
    pass


class TestAC5DryRunNoSideEffects(_TestAC5):
    pass
