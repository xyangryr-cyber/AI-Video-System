"""Tests for [SPEC-B-007] agent_call_log table and cost aggregation (aggregator-shim).

Delegates to the real test module listed in the task card's ``allowed_files``:
- tests/unit/infra/test_agent_call_log.py (AC-1..AC-5)

Re-exports via class-inheritance so the task-card verification command
``pytest tests/unit/infra/test_spec_b_007.py`` runs the real assertions
(A-100..A-105 / B-015 / B-016 precedent).
"""

from __future__ import annotations

from tests.unit.infra.test_agent_call_log import (
    conn,  # noqa: F401 -- re-export so pytest resolves the `conn` fixture
    TestAC1AutoLogOnLlmCall as _TestAC1,
    TestAC2TokensPositiveDurationMeasured as _TestAC2,
    TestAC3ByPhaseSumEqualsTotal as _TestAC3,
    TestAC4CostWarnAt15Dollars as _TestAC4,
    TestAC5NoCircuitBreakerV1 as _TestAC5,
)


class TestAC1AutoLogOnLlmCall(_TestAC1):
    pass


class TestAC2TokensPositiveDurationMeasured(_TestAC2):
    pass


class TestAC3ByPhaseSumEqualsTotal(_TestAC3):
    pass


class TestAC4CostWarnAt15Dollars(_TestAC4):
    pass


class TestAC5NoCircuitBreakerV1(_TestAC5):
    pass
