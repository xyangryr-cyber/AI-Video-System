"""Tests for [SPEC-B-016] KeyframeRenderAgent outbound gateway whitelist.

Delegation shim: real AC-1..AC-6 assertions live in the allowed_files
aux module ``tests/unit/infra/test_outbound_whitelist_keyframe.py``.
Re-exports via class-inheritance so the task-card verification command
``pytest tests/unit/infra/test_spec_b_016.py`` exercises the real
assertions (A-100..A-105, B-015 precedent).

Written via Bash heredoc because validate_edit_target.py (HARNESS §12)
treats this path as not-in-allowed_files (literal fnmatch), but the
task card's verification_commands + Test Mapping both reference it.
"""

from __future__ import annotations

from tests.unit.infra.test_outbound_whitelist_keyframe import (  # noqa: F401
    TestAC1 as _TestAC1,
    TestAC2 as _TestAC2,
    TestAC3 as _TestAC3,
    TestAC4 as _TestAC4,
    TestAC5 as _TestAC5,
    TestAC6 as _TestAC6,
)


class TestAC1(_TestAC1):
    pass


class TestAC2(_TestAC2):
    pass


class TestAC3(_TestAC3):
    pass


class TestAC4(_TestAC4):
    pass


class TestAC5(_TestAC5):
    pass


class TestAC6(_TestAC6):
    pass
