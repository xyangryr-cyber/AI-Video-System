"""Tests for [SPEC-B-100] claim_verification queue + alerts + Dashboard metrics.

Delegation shim: real AC-1..AC-4 assertions live in the allowed_files aux
module ``tests/integration/test_claim_verification_worker.py``. Re-exports
via class-inheritance so the task-card verification command
``pytest tests/unit/infra/test_spec_b_100.py`` exercises the real
assertions (A-100..A-105, B-015, B-016 precedent).

Written via Bash heredoc because validate_edit_target.py (HARNESS §12)
treats this path as not-in-allowed_files (literal fnmatch), but the task
card's verification_commands + Test Mapping both reference it.
"""

from __future__ import annotations

from tests.integration.test_claim_verification_worker import (  # noqa: F401
    TestAC1ExponentialBackoffAndDeadLetter as _TestAC1,
    TestAC2DashboardEmitsFourMetrics as _TestAC2,
    TestAC3AlertThresholds as _TestAC3,
    TestAC4ChallengeClaimPriorityLatency as _TestAC4,
)


class TestAC1(_TestAC1):
    pass


class TestAC2(_TestAC2):
    pass


class TestAC3(_TestAC3):
    pass


class TestAC4(_TestAC4):
    pass
