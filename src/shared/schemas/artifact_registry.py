"""Artifact registry mapping artifact names to producer / consumers / validation.

Source of truth: docs/specs/SPEC-A-contracts.md SPEC-0A.1 table, extended by
SPEC-A-013 (A-AUDP7A-1) with three master-audio entries, by
SPEC-A-014 (A-AUDP7A-2) with two SFX entries (layout plan + mix segments),
by SPEC-A-015 (A-AUDP7A-3) with two P7A material-manifest entries, and by
SPEC-A-016 (A-AUDP7A-4) with one P7A chart-material entry.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactEntry:
    producer: str
    consumers: tuple[str, ...]
    validation: str


ARTIFACT_REGISTRY: dict[str, ArtifactEntry] = {
    "requirements.json": ArtifactEntry(
        producer="P0/RequirementsAgent",
        consumers=("P1-P11",),
        validation="CompletenessReviewer + JSON Schema",
    ),
    "outline": ArtifactEntry(
        producer="P1/OutlineAgent",
        consumers=("P2/ScriptAgent",),
        validation="StructureReviewer",
    ),
    "polished_script": ArtifactEntry(
        producer="P3/PolishAgent",
        consumers=("P4/TTSAgent", "P7/StoryboardAgent", "P10/SubtitleRenderer"),
        validation="StyleReviewer",
    ),
    "timeline.json": ArtifactEntry(
        producer="P4/TTSAgent",
        consumers=("P7/StoryboardAgent", "P10/RoughCutAgent", "F/SubtitleRenderer"),
        validation="AudioQualityReviewer",
    ),
    "style_lock.json": ArtifactEntry(
        producer="P7/StoryboardAgent",
        consumers=("P8/KeyframeRenderAgent", "F/ThemeConfig"),
        validation="StoryboardReviewer",
    ),
    "keyframe_renders": ArtifactEntry(
        producer="P8/KeyframeRenderAgent",
        consumers=("P10/RoughCutAgent",),
        validation="VisualReviewer",
    ),
    "rough_cut": ArtifactEntry(
        producer="P10/RoughCutAgent",
        consumers=("P11/FinalCutAgent",),
        validation="AVSyncReviewer",
    ),
    "final_cut": ArtifactEntry(
        producer="P11/FinalCutAgent",
        consumers=("user_download",),
        validation="FinalReviewer",
    ),
    # -------- SPEC-A-013 (A-AUDP7A-1) master-audio entries ------------------
    "phase_4/narration_master.mp3": ArtifactEntry(
        producer="NarrationMasterAssembler",
        consumers=(
            "P5/BgmMixRenderer",
            "P6/SfxSegmentMixService",
            "frontend/P4MasterPlayer",
        ),
        validation="audio_master.schema.json + ffprobe",
    ),
    "phase_5/bgm_mix_master.mp3": ArtifactEntry(
        producer="BgmMixRenderer",
        consumers=(
            "P6/SfxSegmentMixService",
            "frontend/P5MasterPlayer",
        ),
        validation=(
            "audio_master.schema.json + checksum chain back to narration_master"
        ),
    ),
    "phase_6/final_audio_with_bgm_sfx.mp3": ArtifactEntry(
        producer="FinalAudioAssembler",
        consumers=(
            "P7/StoryboardAgent",
            "P10/RoughCutAgent",
            "P11/FinalCutAgent",
            "frontend/P6MasterPlayer",
        ),
        validation=("audio_master.schema.json + checksum chain back to bgm_mix_master"),
    ),
    # -------- SPEC-A-014 (A-AUDP7A-2) SFX dual-layer entries ----------------
    "phase_6/sfx_layout_plan.json": ArtifactEntry(
        producer="SfxLayoutPlanner",
        consumers=(
            "SfxLayoutReviewer",
            "frontend/P6FullTextAnnotationView",
        ),
        validation="sfx_layout_plan.schema.json + L1 program check",
    ),
    "phase_6/sfx_mix_segments.json": ArtifactEntry(
        producer="SfxSegmentMixService",
        consumers=(
            "FinalAudioAssembler",
            "SfxMixReviewer",
        ),
        validation=(
            "sfx_mix_segments.schema.json + checksum chain back to base_master"
        ),
    ),
    # -------- SPEC-A-015 (A-AUDP7A-3) P7A material-manifest entries ---------
    "phase_7a/material_manifest.json": ArtifactEntry(
        producer="StoryboardAssetPlanner / MaterialFetcher / MaterialVerifier",
        consumers=(
            "P8/MaterialReadinessCheck",
            "frontend/P7AShotMaterialMatrix",
        ),
        validation="material_manifest.schema.json",
    ),
    "phase_7a/shot_material_bindings.json": ArtifactEntry(
        producer="StoryboardAssetPlanner",
        consumers=(
            "P8/KeyframeRenderAgent",
            "frontend/P7AShotMaterialMatrix",
        ),
        validation="shot_material_bindings.schema.json",
    ),
    # -------- SPEC-A-016 (A-AUDP7A-4) P7A chart-material entry --------------
    "phase_7a/chart_materials/chart_*.json": ArtifactEntry(
        producer="StoryboardAssetPlanner / FinancialDataService",
        consumers=(
            "P8/KeyframeRenderAgent",
            "template/ChartIntent",
        ),
        validation="chart_material.schema.json + axis_spec L1 check",
    ),
}

__all__ = ["ARTIFACT_REGISTRY", "ArtifactEntry"]
