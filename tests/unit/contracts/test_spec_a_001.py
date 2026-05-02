"""Tests for [SPEC-A-001] Artifact JSON Schemas (requirements, timeline, style_lock)."""

from __future__ import annotations

from tests.unit.contracts.test_artifact_schemas import (
    TestAC1RequirementsJsonSchema as _TestAC1RequirementsJsonSchema,
    TestAC2TimelineJsonSchema as _TestAC2TimelineJsonSchema,
    TestAC3StyleLockJsonSchema as _TestAC3StyleLockJsonSchema,
    TestAC4PydanticRoundTrip as _TestAC4PydanticRoundTrip,
    TestAC5TypeScriptInterfacesMatchPydantic as _TestAC5TypeScriptInterfacesMatchPydantic,
    TestAC6ArtifactRegistryCoversAll8 as _TestAC6ArtifactRegistryCoversAll8,
)


CORE_ARTIFACTS = {
    "requirements.json",
    "outline",
    "polished_script",
    "timeline.json",
    "style_lock.json",
    "keyframe_renders",
    "rough_cut",
    "final_cut",
}


class TestAC1RequirementsJsonSchema(_TestAC1RequirementsJsonSchema):
    pass


class TestAC2TimelineJsonSchema(_TestAC2TimelineJsonSchema):
    pass


class TestAC3StyleLockJsonSchema(_TestAC3StyleLockJsonSchema):
    pass


class TestAC4PydanticRoundTrip(_TestAC4PydanticRoundTrip):
    pass


class TestAC5TypeScriptInterfacesMatchPydantic(
    _TestAC5TypeScriptInterfacesMatchPydantic
):
    pass


class TestAC6ArtifactRegistryCoversAll8(_TestAC6ArtifactRegistryCoversAll8):
    def test_artifact_registry_covers_all_8(self):
        from src.shared.schemas.artifact_registry import ARTIFACT_REGISTRY

        missing = CORE_ARTIFACTS - set(ARTIFACT_REGISTRY)
        assert not missing, f"Missing core artifact registry entries: {sorted(missing)}"

        for name in CORE_ARTIFACTS:
            entry = ARTIFACT_REGISTRY[name]
            assert entry.producer, f"{name} missing producer"
            assert entry.consumers, f"{name} missing consumers"
            assert entry.validation, f"{name} missing validation"
