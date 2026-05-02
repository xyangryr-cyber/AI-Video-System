"""Tests for [SPEC-C-101] IntentRouter 6 new actions.

Real tests in tests/unit/agents/test_intent_router_v316.py.
Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_agt_irv = SourceFileLoader(
    "test_intent_router_v316",
    str(_dir.parent / "agents" / "test_intent_router_v316.py"),
).load_module()


class TestAC1(_agt_irv.TestAC1):
    pass


class TestAC2(_agt_irv.TestAC2):
    pass


class TestAC3(_agt_irv.TestAC3):
    pass
