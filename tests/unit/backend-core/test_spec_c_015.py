"""Tests for [SPEC-C-015] GateKeeper (7-Item Gate Check + Skip Branch + Claude Model).

Real tests in test_gatekeeper.py. Re-exports for canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_ = SourceFileLoader("test_gatekeeper", str(_dir / "test_gatekeeper.py")).load_module()

conn = _.conn


class TestAC1EachCheckFailsIndependently(_.TestAC1EachCheckFailsIndependently):
    pass


class TestAC2AllPassAdvanceSucceeds(_.TestAC2AllPassAdvanceSucceeds):
    pass


class TestAC3NoShortCircuitAllFailures(_.TestAC3NoShortCircuitAllFailures):
    pass


class TestAC4SkipChecksOnly4And6(_.TestAC4SkipChecksOnly4And6):
    pass


class TestAC5SkipNoArtifactOk(_.TestAC5SkipNoArtifactOk):
    pass


class TestAC6SkipInProgressBlocks(_.TestAC6SkipInProgressBlocks):
    pass


class TestAC7VerdictBinaryPassFail(_.TestAC7VerdictBinaryPassFail):
    pass


class TestAC8GatekeeperUsesClaudeModel(_.TestAC8GatekeeperUsesClaudeModel):
    pass


class TestAC9CallLogMatchesConfig(_.TestAC9CallLogMatchesConfig):
    pass


class TestAC10CostCheckNonBlocking(_.TestAC10CostCheckNonBlocking):
    pass
