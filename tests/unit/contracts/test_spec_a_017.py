"""Tests for [SPEC-A-017] API GET /artifacts/master_audio + FSM phase_7a 枚举."""

from __future__ import annotations

from tests.unit.contracts.test_master_audio_api import (
    TestAC1RouteDefinition as _TestAC1RouteDefinition,
    TestAC2ResponseFieldsMatchMasterAudioArtifact as _TestAC2ResponseFieldsMatchMasterAudioArtifact,
    TestAC3ErrorCodes as _TestAC3ErrorCodes,
)
from tests.unit.contracts.test_phase_enum import (
    TestAC4PhaseIdEnum as _TestAC4PhaseIdEnum,
    TestAC5PhaseDetailSupportsPhase7a as _TestAC5PhaseDetailSupportsPhase7a,
    TestAC6PhasesTableColumnAllowsPhase7a as _TestAC6PhasesTableColumnAllowsPhase7a,
)


class TestAC1(_TestAC1RouteDefinition):
    pass


class TestAC2(_TestAC2ResponseFieldsMatchMasterAudioArtifact):
    pass


class TestAC3(_TestAC3ErrorCodes):
    pass


class TestAC4(_TestAC4PhaseIdEnum):
    pass


class TestAC5(_TestAC5PhaseDetailSupportsPhase7a):
    pass


class TestAC6(_TestAC6PhasesTableColumnAllowsPhase7a):
    pass
