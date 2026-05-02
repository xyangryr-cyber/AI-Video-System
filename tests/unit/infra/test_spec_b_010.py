"""Tests for [SPEC-B-010] Four-Type Observability Evidence and Alert System (aggregator-shim).

Delegates to the real test modules listed in the task card's ``allowed_files``:
- tests/unit/infra/test_observability.py (AC-1, AC-2)
- tests/unit/infra/test_alerts.py (AC-3..AC-6)

Re-exports via class-inheritance so the task-card verification command
``pytest tests/unit/infra/test_spec_b_010.py`` runs the real assertions
(A-100..A-105 / B-015 / B-016 / B-007 / B-008 precedent).
"""

from __future__ import annotations

from tests.unit.infra.test_alerts import (
    conn,  # noqa: F401 -- re-export so pytest resolves the `conn` fixture
    TestAC3QueueBuildupAlert as _TestAC3,
    TestAC4AlertHasOwnerField as _TestAC4,
    TestAC5AlertLogFormatSpec13B as _TestAC5,
    TestAC6DefaultAlertThresholds as _TestAC6,
)
from tests.unit.infra.test_observability import (
    TestAC1FourEvidenceTypesNonEmpty as _TestAC1,
    TestAC2PhaseConsistencyWithEvents as _TestAC2,
)


class TestAC1FourEvidenceTypesNonEmpty(_TestAC1):
    pass


class TestAC2PhaseConsistencyWithEvents(_TestAC2):
    pass


class TestAC3QueueBuildupAlert(_TestAC3):
    pass


class TestAC4AlertHasOwnerField(_TestAC4):
    pass


class TestAC5AlertLogFormatSpec13B(_TestAC5):
    pass


class TestAC6DefaultAlertThresholds(_TestAC6):
    pass
