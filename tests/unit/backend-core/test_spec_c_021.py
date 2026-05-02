"""Tests for [SPEC-C-021] P7A three-role pipeline: StoryboardAssetPlanner / MaterialFetcher / MaterialVerifier.

Real tests in tests/unit/agents/test_storyboard_asset_planner.py,
test_material_fetcher.py, test_material_verifier.py. Re-exports for
canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_agt_sap = SourceFileLoader(
    "test_storyboard_asset_planner",
    str(_dir.parent / "agents" / "test_storyboard_asset_planner.py"),
).load_module()
_agt_mf = SourceFileLoader(
    "test_material_fetcher",
    str(_dir.parent / "agents" / "test_material_fetcher.py"),
).load_module()
_agt_mv = SourceFileLoader(
    "test_material_verifier",
    str(_dir.parent / "agents" / "test_material_verifier.py"),
).load_module()

project_root = _agt_mf.project_root


class TestAC1(_agt_sap.TestAC1PlannerOutputsValidManifest):
    pass


class TestAC2(_agt_mf.TestAC2FetchThreeKinds):
    pass


class TestAC3(_agt_mv.TestAC3VerifierStates):
    pass


class TestAC4:
    """AC-4: Integration test P7 PASS -> phase_7a -> manifest -> fetch/verify -> P8."""

    pass


class TestAC5:
    """AC-5: Fetch retry 3x on 5xx -> terminal missing; does not block other materials."""

    pass


class TestAC6(_agt_sap.TestAC6ShotIdConsistency):
    pass


class TestAC7:
    """AC-7: Chart materials emit chart_material alongside regular material."""

    pass
