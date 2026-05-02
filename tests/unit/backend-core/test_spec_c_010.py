"""Tests for [SPEC-C-010] Reviewer Agent & Dual-Layer Architecture (L1 + L2).

Real tests in test_reviewer_agent.py. Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_ = SourceFileLoader(
    "test_reviewer_agent", str(_dir / "test_reviewer_agent.py")
).load_module()


class TestAC1VerdictOnlyPassOrFail(_.TestAC1VerdictOnlyPassOrFail):
    pass


class TestAC2BlockingIssuesImpliesFail(_.TestAC2BlockingIssuesImpliesFail):
    pass


class TestAC3L1FailSkipsL2(_.TestAC3L1FailSkipsL2):
    pass


class TestAC4PureL1ZeroTokens(_.TestAC4PureL1ZeroTokens):
    pass


class TestAC5HybridL2AfterL1Pass(_.TestAC5HybridL2AfterL1Pass):
    pass


class TestAC6TwelveReviewersRegistered(_.TestAC6TwelveReviewersRegistered):
    pass
