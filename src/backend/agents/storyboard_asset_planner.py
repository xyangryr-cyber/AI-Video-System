"""[SPEC-C-021] StoryboardAssetPlanner (LLM Planner).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-6.

Given the P7 storyboard (list of StoryboardShotAnchor) and the 7-state
ChartRequest list, emit a MaterialManifest that lists every asset the
pipeline needs to fetch in P7A. The planner does NOT fetch anything —
it only decides *what* to fetch. Subsequent stages (MaterialFetcher,
MaterialVerifier) update verification_status through the A-015 state
machine.

Implementation notes
--------------------
* In V1 the planner is deterministic: one CHART material per
  ChartRequest and one FACT material per shot. A later iteration can
  swap the deterministic skeleton for an Instructor-validated LLM call
  via :mod:`src.backend.services.llm_service`. The point of SPEC-C-021
  is to lock down the manifest shape, fetch/verify wiring, and shot_id
  invariant — not the LLM's cleverness.
* Every emitted material is PENDING; ``fetched_at`` is the sentinel
  ``"pending"`` so the MaterialEntry schema's ``min_length=1``
  constraint is satisfied while still being distinguishable from a
  real ISO-8601 timestamp.
* ``validate_shot_ids_in_anchors`` is the public guard behind AC-6:
  callers in the orchestrator invoke it after the planner returns and
  again before every Fetcher dispatch, so a bad shot_id cannot sneak
  in via a hand-authored manifest either.
"""

from __future__ import annotations

from collections.abc import Iterable

from src.shared.schemas.chart_material import derive_chart_id_from_request_id
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


class StoryboardAssetPlanner:
    """Stateless P7A asset planner."""

    @staticmethod
    def plan(
        *,
        project_id: str,
        shots: list[StoryboardShotAnchor] | Iterable[StoryboardShotAnchor],
        chart_requests: list[ChartRequest] | Iterable[ChartRequest],
    ) -> MaterialManifest:
        shots = list(shots)
        chart_requests = list(chart_requests)

        materials: list[MaterialEntry] = []
        seq = 1

        # One CHART material per ChartRequest. The chart_id is derived
        # from request_id via the canonical A-016 mapping so downstream
        # consumers can round-trip the link.
        for idx, req in enumerate(chart_requests):
            if not shots:
                raise ValueError("cannot plan chart materials without storyboard shots")
            anchor = shots[idx % len(shots)]
            chart_id = derive_chart_id_from_request_id(req.request_id)
            materials.append(
                MaterialEntry(
                    material_id=f"mat_{seq:03d}",
                    shot_id=anchor.shot_id,
                    material_type=MaterialType.CHART,
                    required=RequiredLevel.HARD,
                    source=MaterialSource(
                        kind=SourceKind.API,
                        ref=req.request_id,
                    ),
                    verification_status=VerificationStatus.PENDING,
                    fetched_at="pending",
                    rationale=(f"chart for {req.user_intent}; linked chart_id={chart_id}"),
                )
            )
            seq += 1

        # One FACT material per shot — the non-chart baseline (AC-1b).
        for anchor in shots:
            materials.append(
                MaterialEntry(
                    material_id=f"mat_{seq:03d}",
                    shot_id=anchor.shot_id,
                    material_type=MaterialType.FACT,
                    required=RequiredLevel.SOFT,
                    source=MaterialSource(
                        kind=SourceKind.API,
                        ref=f"fact:{anchor.shot_id}",
                    ),
                    verification_status=VerificationStatus.PENDING,
                    fetched_at="pending",
                    rationale=(
                        f"supporting fact for shot {anchor.shot_id}; anchor={anchor.anchor_text!r}"
                    ),
                )
            )
            seq += 1

        manifest = MaterialManifest(
            project_id=project_id,
            phase="7A",
            materials=materials,
        )
        # AC-6 is enforced at construction time too.
        StoryboardAssetPlanner.validate_shot_ids_in_anchors(manifest=manifest, anchors=shots)
        return manifest

    @staticmethod
    def validate_shot_ids_in_anchors(
        *,
        manifest: MaterialManifest,
        anchors: list[StoryboardShotAnchor] | Iterable[StoryboardShotAnchor],
    ) -> None:
        """AC-6: every material.shot_id must be in the anchor set.

        Raises ValueError on first offending material_id.
        """
        allowed = {a.shot_id for a in anchors}
        for m in manifest.materials:
            if m.shot_id not in allowed:
                raise ValueError(
                    f"material {m.material_id!r} has shot_id={m.shot_id!r} "
                    f"not present in StoryboardShotAnchor set {sorted(allowed)}"
                )


__all__ = ["StoryboardAssetPlanner"]
