"""Tests for [SPEC-C-009] Producer Agent Template, Streaming & Decision Rationale.

Real tests in test_producer_agent.py. Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_ = SourceFileLoader(
    "test_producer_agent", str(_dir / "test_producer_agent.py")
).load_module()


class TestAC1TemplateHasSevenFields(_.TestAC1TemplateHasSevenFields):
    pass


class TestAC2MissingFieldRaises(_.TestAC2MissingFieldRaises):
    pass


class TestAC3TtftUnder3s(_.TestAC3TtftUnder3s):
    pass


class TestAC4StreamedTokensEqualFinal(_.TestAC4StreamedTokensEqualFinal):
    pass


class TestAC5DecisionRationaleRequired(_.TestAC5DecisionRationaleRequired):
    pass


class TestAC6MissingRationaleRetries(_.TestAC6MissingRationaleRetries):
    pass
