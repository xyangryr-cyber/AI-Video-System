"""Tests for [SPEC-B-012] Non-Functional Requirements (aggregator-shim).

Delegates to the real test module listed in the task card's ``allowed_files``:
- tests/unit/infra/test_nonfunctional.py (AC-1..AC-7)

Re-exports via class-inheritance so the task-card verification command
``pytest tests/unit/infra/test_spec_b_012.py`` runs the real assertions.
"""

from __future__ import annotations

from tests.unit.infra.test_nonfunctional import (
    TestAC1SingleTabRejectsSecondConnection as _TestAC1,
    TestAC2RegenerateLimitSuggestsManualEdit as _TestAC2,
    TestAC3NoSyncWaitInHandlers as _TestAC3,
    TestAC4NoHardcodedApiKeys as _TestAC4,
    TestAC5EvalDirectoryWithJsonlTemplates as _TestAC5,
    TestAC6CiPathFilterConfigured as _TestAC6,
    TestAC7PipelineSkeletonRuns as _TestAC7,
)


class TestAC1SingleTabRejectsSecondConnection(_TestAC1):
    pass


class TestAC2RegenerateLimitSuggestsManualEdit(_TestAC2):
    pass


class TestAC3NoSyncWaitInHandlers(_TestAC3):
    pass


class TestAC4NoHardcodedApiKeys(_TestAC4):
    pass


class TestAC5EvalDirectoryWithJsonlTemplates(_TestAC5):
    pass


class TestAC6CiPathFilterConfigured(_TestAC6):
    pass


class TestAC7PipelineSkeletonRuns(_TestAC7):
    pass
