"""Tests for [SPEC-C-001] WorkflowEngine Single-Class Implementation.

Real tests are implemented in test_workflow_engine.py.
This file re-exports them for canonical test discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_ = SourceFileLoader(
    "test_workflow_engine", str(_dir / "test_workflow_engine.py")
).load_module()


class TestAC1AllStateChangesThroughEngine(_.TestAC1AllStateChangesThroughEngine):
    pass


class TestAC2EventBusPureFunction(_.TestAC2EventBusPureFunction):
    pass


class TestAC3EngineReadsProjectsPhasesLedger(_.TestAC3EngineReadsProjectsPhasesLedger):
    pass


class TestAC4EngineWritesCorrectTables(_.TestAC4EngineWritesCorrectTables):
    pass


class TestAC5ClassFileUnder400Lines(_.TestAC5ClassFileUnder400Lines):
    pass
