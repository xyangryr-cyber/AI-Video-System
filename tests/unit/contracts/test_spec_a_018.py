"""Tests for [SPEC-A-018] 错误码 render_failed / material_missing / material_unverified + WebSocket phase.shot_blocked 事件."""

from __future__ import annotations

from tests.unit.contracts.test_error_codes_v317 import (
    TestAC1 as _TestAC1ErrorCodesV317,
    TestAC3 as _TestAC3ErrorCodesV317,
    TestAC4 as _TestAC4ErrorCodesV317,
)
from tests.unit.contracts.test_phase_shot_blocked_event import (
    TestAC2 as _TestAC2PhaseShotBlockedEvent,
    TestAC5 as _TestAC5PhaseShotBlockedEvent,
)


class TestAC1(_TestAC1ErrorCodesV317):
    pass


class TestAC2(_TestAC2PhaseShotBlockedEvent):
    pass


class TestAC3(_TestAC3ErrorCodesV317):
    pass


class TestAC4(_TestAC4ErrorCodesV317):
    pass


class TestAC5(_TestAC5PhaseShotBlockedEvent):
    pass
