"""Tests for [SPEC-B-008] Sensitive Field Redaction and Leak Scan (aggregator-shim).

Delegates to the real test module listed in the task card's ``allowed_files``:
- tests/unit/infra/test_redaction.py (AC-1..AC-5)

Re-exports via class-inheritance so the task-card verification command
``pytest tests/unit/infra/test_spec_b_008.py`` runs the real assertions
(A-100..A-105 / B-015 / B-016 / B-007 precedent).
"""

from __future__ import annotations

from tests.unit.infra.test_redaction import (
    conn,  # noqa: F401 -- re-export so pytest resolves the `conn` fixture
    TestAC1SkPrefixRedacted as _TestAC1,
    TestAC2SecretRegexesCount7 as _TestAC2,
    TestAC3LargePayloadTruncation as _TestAC3,
    TestAC4LeakScanZeroHits as _TestAC4,
    TestAC5RedactionBeforeDbWrite as _TestAC5,
)


class TestAC1SkPrefixRedacted(_TestAC1):
    pass


class TestAC2SecretRegexesCount7(_TestAC2):
    pass


class TestAC3LargePayloadTruncation(_TestAC3):
    pass


class TestAC4LeakScanZeroHits(_TestAC4):
    pass


class TestAC5RedactionBeforeDbWrite(_TestAC5):
    pass
