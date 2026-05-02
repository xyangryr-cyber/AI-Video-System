"""Tests for [SPEC-C-002] Task Data Structures & State Machine.

Real tests in test_task_types.py and test_state_machine.py.
Re-exports for canonical test discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_tt = SourceFileLoader(
    "test_task_types", str(_dir / "test_task_types.py")
).load_module()
_sm = SourceFileLoader(
    "test_state_machine", str(_dir / "test_state_machine.py")
).load_module()


class TestAC1TaskIdFormat(_tt.TestAC1TaskIdFormat):
    pass


class TestAC2FieldConstraintsByTaskType(_tt.TestAC2FieldConstraintsByTaskType):
    pass


class TestAC3EightTaskTypesEnumerated(_tt.TestAC3EightTaskTypes):
    pass


class TestAC4SucceededToRunningRaises(_sm.TestAC4SucceededToRunningRaises):
    pass


class TestAC5FailedToQueuedRaises(_sm.TestAC5FailedToQueuedRaises):
    pass


class TestAC6AllLegalTransitionsPass(_sm.TestAC6AllLegalTransitions):
    pass


class TestAC7LegalTransitionWritesEvent(_sm.TestAC7TransitionWritesEvent):
    pass


class TestAC8StaleReviewSuperseded(_sm.TestAC8StaleReviewSuperseded):
    pass
