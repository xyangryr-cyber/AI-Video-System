"""Tests for [SPEC-A-103] ChartRequest / AxisSpec / ChartStyleOverrides / StoryboardShotAnchor.

Delegates to the two aux modules listed in the task card's ``allowed_files``
(``test_chart_schemas.py`` + ``test_shot_anchor_schema.py``). Mirrors the
A-100 / A-101 / A-102 pattern so the task-card ``verification_commands``
(``pytest tests/unit/contracts/test_spec_a_103.py``) runs the real
AC-1..AC-4 assertions rather than the prior ``pytest.skip`` stubs.
"""

from __future__ import annotations

from tests.unit.contracts.test_chart_schemas import (
    TestAC1ChartRequestStatusEnum as _TestAC1,
    TestAC2AxisSpecZeroBased as _TestAC2,
)
from tests.unit.contracts.test_shot_anchor_schema import (
    TestAC3StoryboardShotAnchorMandatoryFields as _TestAC3,
    TestAC4DownstreamBindingsOptional as _TestAC4,
)


class TestAC1(_TestAC1):
    pass


class TestAC2(_TestAC2):
    pass


class TestAC3(_TestAC3):
    pass


class TestAC4(_TestAC4):
    pass
