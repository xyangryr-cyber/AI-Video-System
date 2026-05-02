"""[SPEC-C-021] StoryboardAssetPlanner unit tests.

Covers AC-1 (manifest validity + chart/non-chart coverage) and AC-6
(shot_id consistency with StoryboardShotAnchor set). AC-7 (chart_material
side-product) is exercised at the orchestrator level because it depends
on fetcher/verifier wiring.
"""

from __future__ import annotations

import pytest

from src.backend.agents.storyboard_asset_planner import StoryboardAssetPlanner
from src.shared.schemas.chart_request import ChartRequest
from src.shared.schemas.material_manifest import (
    MaterialEntry,
    MaterialManifest,
    MaterialSource,
    MaterialType,
    RequiredLevel,
    SourceKind,
    VerificationStatus,
)
from src.shared.schemas.storyboard_shot_anchor import StoryboardShotAnchor


def _anchor(shot_id: str, start: int = 0, end: int = 10) -> StoryboardShotAnchor:
    return StoryboardShotAnchor(
        shot_id=shot_id,
        anchor_text="anchor-text-" + shot_id,
        script_span_id="span_" + shot_id,
        start_char=start,
        end_char=end,
    )


def _chart_request(request_id: str = "req_001") -> ChartRequest:
    return ChartRequest(
        request_id=request_id,
        user_intent="line chart of AAPL 2024 close price",
        chart_type="line",
        status="awaiting_verification",
    )


def _pending_entry(
    *,
    material_id: str,
    shot_id: str,
    kind: SourceKind = SourceKind.API,
    material_type: MaterialType = MaterialType.FACT,
    ref: str = "r",
) -> MaterialEntry:
    return MaterialEntry(
        material_id=material_id,
        shot_id=shot_id,
        material_type=material_type,
        required=RequiredLevel.HARD,
        source=MaterialSource(kind=kind, ref=ref),
        verification_status=VerificationStatus.PENDING,
        fetched_at="pending",
        rationale="needed for storyboard",
    )


# -- AC-1 ---------------------------------------------------------------


class TestAC1PlannerOutputsValidManifest:
    def test_planner_outputs_valid_manifest(self) -> None:
        manifest = StoryboardAssetPlanner.plan(
            project_id="proj_001",
            shots=[_anchor("shot_01"), _anchor("shot_02")],
            chart_requests=[_chart_request("req_001")],
        )
        # Round-trip schema validates.
        MaterialManifest.model_validate(manifest.model_dump())
        assert manifest.project_id == "proj_001"
        assert manifest.phase == "7A"
        assert len(manifest.materials) >= 2

    def test_includes_chart_and_non_chart(self) -> None:
        manifest = StoryboardAssetPlanner.plan(
            project_id="proj_001",
            shots=[_anchor("shot_01"), _anchor("shot_02")],
            chart_requests=[_chart_request("req_001")],
        )
        kinds = {m.material_type for m in manifest.materials}
        assert MaterialType.CHART in kinds
        assert kinds - {MaterialType.CHART}, "must emit at least one non-chart material"


# -- AC-6 ---------------------------------------------------------------


class TestAC6ShotIdConsistency:
    def test_negative_shot_id_raises(self) -> None:
        anchors = [_anchor("shot_01")]
        bad_manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[_pending_entry(material_id="mat_901", shot_id="shot_99")],
        )
        with pytest.raises(ValueError, match="shot_id"):
            StoryboardAssetPlanner.validate_shot_ids_in_anchors(
                manifest=bad_manifest, anchors=anchors
            )

    def test_positive_shot_id_ok(self) -> None:
        anchors = [_anchor("shot_01")]
        good_manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[_pending_entry(material_id="mat_902", shot_id="shot_01")],
        )
        # No raise.
        StoryboardAssetPlanner.validate_shot_ids_in_anchors(
            manifest=good_manifest, anchors=anchors
        )
