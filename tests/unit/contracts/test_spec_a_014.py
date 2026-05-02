"""Tests for [SPEC-A-014] SfxLayoutPlan + SfxMixSegments schemas（P6 双层模型）."""

from __future__ import annotations

from tests.unit.contracts.test_sfx_schemas import (
    TestAC1JsonSchemaPayloads as _TestAC1JsonSchemaPayloads,
    TestAC2PydanticTsAlignment as _TestAC2PydanticTsAlignment,
    TestAC3BaseMasterPattern as _TestAC3BaseMasterPattern,
    TestAC4RegistryEntries as _TestAC4RegistryEntries,
    TestAC5CrossArtifactConsistency as _TestAC5CrossArtifactConsistency,
)


class TestAC1(_TestAC1JsonSchemaPayloads):
    pass


class TestAC2(_TestAC2PydanticTsAlignment):
    pass


class TestAC3(_TestAC3BaseMasterPattern):
    pass


class TestAC4(_TestAC4RegistryEntries):
    pass


class TestAC5(_TestAC5CrossArtifactConsistency):
    pass
