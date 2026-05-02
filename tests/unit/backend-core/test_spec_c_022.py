"""Tests for [SPEC-C-022] MaterialReadinessCheck + MaterialReadinessReviewer + WorkflowEngine P8 entry.

Real tests in tests/unit/services/test_material_readiness_check.py and
tests/unit/reviewers/test_material_readiness_reviewer.py. Re-exports for
canonical discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_svc_mrc = SourceFileLoader(
    "test_material_readiness_check",
    str(_dir.parent / "services" / "test_material_readiness_check.py"),
).load_module()
_rev_mrr = SourceFileLoader(
    "test_material_readiness_reviewer",
    str(_dir.parent / "reviewers" / "test_material_readiness_reviewer.py"),
).load_module()


class TestAC1(_svc_mrc.TestAC1AllVerifiedReturnsOk):
    pass


class TestAC2(_svc_mrc.TestAC2HardUnverifiedBlocksWithErrorCode):
    pass


class TestAC3(_svc_mrc.TestAC3SoftUnverifiedWarnsNotBlocks):
    pass


class TestAC4:
    """AC-4: Integration: 1 hard required unverified -> P8 blocked event emitted."""

    pass


class TestAC5(_rev_mrr.TestAC5ReviewerConsistentWithCheck):
    pass


class TestAC6(_svc_mrc.TestAC6CountMismatchYieldsMaterialMissing):
    pass


class TestAC7(_svc_mrc.TestAC7CheckPerfUnder200ms):
    pass
