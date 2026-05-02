"""Tests for [SPEC-C-004] Phase Advance, Rollback, Skip & Idempotency.

Real tests in test_phase_advance.py, test_phase_rollback.py, test_phase_skip.py.
Re-exports for canonical test discovery via subclassing.
"""

from __future__ import annotations

from importlib.machinery import SourceFileLoader
from pathlib import Path

_dir = Path(__file__).parent
_pa = SourceFileLoader(
    "test_phase_advance", str(_dir / "test_phase_advance.py")
).load_module()
_pr = SourceFileLoader(
    "test_phase_rollback", str(_dir / "test_phase_rollback.py")
).load_module()
_ps = SourceFileLoader(
    "test_phase_skip", str(_dir / "test_phase_skip.py")
).load_module()


class TestAC1RollbackInvalidatesDownstream(_pr.TestAC1RollbackInvalidatesDownstream):
    pass


class TestAC2SkipNoArtifactRequired(_ps.TestAC2SkipNoArtifactRequired):
    pass


class TestAC3SkipPrerequisites(_ps.TestAC3SkipRequirements):
    pass


class TestAC4RollbackImpactAnalysis(_pr.TestAC4RollbackImpactAnalysis):
    pass


class TestAC5AdvanceIdempotentDuplicate(_pa.TestAC5AdvanceIdempotentDuplicate):
    pass


class TestAC6OptimisticLockConflict(_pa.TestAC6OptimisticLockConflict):
    pass


class TestAC7ConcurrentGateReturns409(_pa.TestAC7ConcurrentGateReturns409):
    pass
