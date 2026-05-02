"""Tests for [SPEC-A-015] MaterialManifest + ShotMaterialBindings schemas（P7A 物料清单契约）."""

from __future__ import annotations

from tests.unit.contracts.test_material_manifest_schema import (
    TestAC1JsonSchemaPayloads as _TestAC1JsonSchemaPayloads,
    TestAC2PydanticTsAlignment as _TestAC2PydanticTsAlignment,
    TestAC3CrossArtifactConsistency as _TestAC3CrossArtifactConsistency,
    TestAC4RegistryEntries as _TestAC4RegistryEntries,
    TestAC5VerificationStatusTransitions as _TestAC5VerificationStatusTransitions,
)


class TestAC1(_TestAC1JsonSchemaPayloads):
    pass


class TestAC2(_TestAC2PydanticTsAlignment):
    pass


class TestAC3(_TestAC3CrossArtifactConsistency):
    pass


class TestAC4(_TestAC4RegistryEntries):
    pass


class TestAC5(_TestAC5VerificationStatusTransitions):
    pass
