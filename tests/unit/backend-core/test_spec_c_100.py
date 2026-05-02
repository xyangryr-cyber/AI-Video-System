"""Tests for [SPEC-C-100] SafetyGuard / SafetyPolicyEngine subsystem.

Real tests in tests/unit/agents/test_safety_policy_engine.py.
Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_agt_spe = SourceFileLoader(
    "test_safety_policy_engine",
    str(_dir.parent / "agents" / "test_safety_policy_engine.py"),
).load_module()

engine = _agt_spe.engine


class TestAC1(_agt_spe.TestAC1):
    pass


class TestAC2(_agt_spe.TestAC2):
    pass


class TestAC3(_agt_spe.TestAC3):
    pass


class TestAC4(_agt_spe.TestAC4):
    pass


class TestAC5(_agt_spe.TestAC5):
    pass
