"""Tests for [SPEC-A-007] SQLite Database Schema DDL (10 Tables)."""

from __future__ import annotations

from tests.unit.contracts.test_database_schema import (
    TestAC1Exactly10Tables as _TestAC1Exactly10Tables,
    TestAC2ProjectsStatusCheck as _TestAC2ProjectsStatusCheck,
    TestAC3PhasesStatusCheck as _TestAC3PhasesStatusCheck,
    TestAC4PhasesUniqueProjectPhase as _TestAC4PhasesUniqueProjectPhase,
    TestAC5TaskLedgerTypeCheck as _TestAC5TaskLedgerTypeCheck,
    TestAC6TaskLedgerStatusCheck as _TestAC6TaskLedgerStatusCheck,
    TestAC7AsyncTasksProgressCheck as _TestAC7AsyncTasksProgressCheck,
    TestAC8AgentCallLogTokensCheck as _TestAC8AgentCallLogTokensCheck,
    TestAC9FinancialCacheUniqueConstraint as _TestAC9FinancialCacheUniqueConstraint,
    TestAC10TimestampDefaults as _TestAC10TimestampDefaults,
    TestAC11TaskParamsAll8Types as _TestAC11TaskParamsAll8Types,
    TestAC12DdlLoadsSuccessfully as _TestAC12DdlLoadsSuccessfully,
)


class TestAC1Exactly10Tables(_TestAC1Exactly10Tables):
    pass


class TestAC2ProjectsStatusCheck(_TestAC2ProjectsStatusCheck):
    pass


class TestAC3PhasesStatusCheck(_TestAC3PhasesStatusCheck):
    pass


class TestAC4PhasesUniqueProjectPhase(_TestAC4PhasesUniqueProjectPhase):
    pass


class TestAC5TaskLedgerTypeCheck(_TestAC5TaskLedgerTypeCheck):
    pass


class TestAC6TaskLedgerStatusCheck(_TestAC6TaskLedgerStatusCheck):
    pass


class TestAC7AsyncTasksProgressCheck(_TestAC7AsyncTasksProgressCheck):
    pass


class TestAC8AgentCallLogTokensCheck(_TestAC8AgentCallLogTokensCheck):
    pass


class TestAC9FinancialCacheUniqueConstraint(_TestAC9FinancialCacheUniqueConstraint):
    pass


class TestAC10TimestampDefaults(_TestAC10TimestampDefaults):
    pass


class TestAC11TaskParamsAll8Types(_TestAC11TaskParamsAll8Types):
    pass


class TestAC12DdlLoadsSuccessfully(_TestAC12DdlLoadsSuccessfully):
    pass
