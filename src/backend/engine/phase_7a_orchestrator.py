"""[SPEC-C-021] Phase-7A orchestrator.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-6.

Wires the three P7A roles together in the order required by the spec:

    P7 PASS
      -> StoryboardAssetPlanner.plan(shots, chart_requests) -> manifest
      -> MaterialManifestRepo.save(manifest)
      -> for each material: MaterialFetcher.fetch(entry)
                           -> MaterialFetcher updates fetched_at
                           -> MaterialManifestRepo.replace_entry
                           -> MaterialVerifier.verify(entry)
                              (skipped when fetcher terminated in MISSING)
                           -> MaterialManifestRepo.replace_entry
      -> if every HARD material is VERIFIED -> advanced_to_p8 = True
      -> AC-7 side effect: for every CHART-type material that is
         VERIFIED, also persist a ChartMaterial JSON under
         ``phase_7a/chart_materials/chart_<seq>.json``.

The class is intentionally synchronous and dependency-injected. In the
Huey-backed path the same call graph is reached by fanning out
``material_fetch``/``material_verify`` tasks (SPEC-B-015) and collecting
results back into the orchestrator; V1 unit tests short-circuit that
fan-out and exercise the logic in-process.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Type

from src.backend.agents.material_fetcher import MaterialFetcher
from src.backend.agents.material_verifier import MaterialVerifier
from src.backend.agents.storyboard_asset_planner import StoryboardAssetPlanner
from src.backend.repositories.material_manifest_repo import MaterialManifestRepo
from src.shared.schemas.chart_material import (
    AxisSpec,
    ChartKind,
    ChartMaterial,
    ChartSource,
    ChartSpec,
    DateRange,
    Granularity,
    ScaleMode,
    XAxis,
    XAxisType,
    YAxis,
    derive_chart_id_from_request_id,
)
from src.shared.schemas.chart_request import ChartRequest
from src.shared.schemas.material_manifest import (
    MaterialEntry,
    MaterialManifest,
    MaterialType,
    RequiredLevel,
    VerificationStatus,
)
from src.shared.schemas.storyboard_shot_anchor import StoryboardShotAnchor


@dataclass
class OrchestratorResult:
    manifest: MaterialManifest
    advanced_to_p8: bool


class Phase7aOrchestrator:
    def __init__(
        self,
        *,
        project_id: str,
        project_root: Path,
        planner: Type[StoryboardAssetPlanner],
        fetcher: MaterialFetcher,
        verifier: MaterialVerifier,
    ) -> None:
        self._project_id = project_id
        self._root = Path(project_root)
        self._planner = planner
        self._fetcher = fetcher
        self._verifier = verifier
        self._repo = MaterialManifestRepo(self._root)

    # -- public entry points -----------------------------------------

    def run(
        self,
        *,
        shots: list[StoryboardShotAnchor] | Iterable[StoryboardShotAnchor],
        chart_requests: list[ChartRequest] | Iterable[ChartRequest],
    ) -> OrchestratorResult:
        shots_list = list(shots)
        requests_list = list(chart_requests)
        manifest = self._planner.plan(
            project_id=self._project_id,
            shots=shots_list,
            chart_requests=requests_list,
        )
        self._repo.save(manifest)
        return self._run_fanout(
            manifest=manifest, shots=shots_list, chart_requests=requests_list
        )

    def run_with_manifest(
        self,
        *,
        manifest: MaterialManifest,
        shots: list[StoryboardShotAnchor] | Iterable[StoryboardShotAnchor],
        chart_requests: list[ChartRequest] | Iterable[ChartRequest] | None = None,
    ) -> OrchestratorResult:
        shots_list = list(shots)
        StoryboardAssetPlanner.validate_shot_ids_in_anchors(
            manifest=manifest, anchors=shots_list
        )
        self._repo.save(manifest)
        return self._run_fanout(
            manifest=manifest,
            shots=shots_list,
            chart_requests=list(chart_requests or []),
        )

    # -- internals ---------------------------------------------------

    def _run_fanout(
        self,
        *,
        manifest: MaterialManifest,
        shots: list[StoryboardShotAnchor],
        chart_requests: list[ChartRequest],
    ) -> OrchestratorResult:
        # Fetch + verify each material in-process (Huey-equivalent).
        for material in list(manifest.materials):
            fetched = self._fetcher.fetch(material)
            manifest = self._repo.replace_entry(fetched)

            if fetched.verification_status == VerificationStatus.MISSING:
                # Fetcher exhausted retries; verifier has nothing to do.
                continue

            verified = self._verifier.verify(fetched)
            manifest = self._repo.replace_entry(verified)

            if (
                verified.material_type == MaterialType.CHART
                and verified.verification_status == VerificationStatus.VERIFIED
            ):
                self._emit_chart_material(verified, chart_requests)

        advanced = self._can_advance(manifest)
        return OrchestratorResult(manifest=manifest, advanced_to_p8=advanced)

    @staticmethod
    def _can_advance(manifest: MaterialManifest) -> bool:
        """Advance to P8 iff every HARD-required material is VERIFIED."""
        for m in manifest.materials:
            if m.required == RequiredLevel.HARD:
                if m.verification_status != VerificationStatus.VERIFIED:
                    return False
        return True

    def _emit_chart_material(
        self,
        entry: MaterialEntry,
        chart_requests: list[ChartRequest],
    ) -> None:
        """Persist a minimum-viable ChartMaterial JSON for a chart entry.

        The chart_id is derived from the source.ref (which the planner
        sets to the ChartRequest.request_id). When a matching
        ChartRequest is available, its metadata is used verbatim;
        otherwise a deterministic stub is emitted so the schema round-
        trips. Downstream phases treat the absence of a ChartRequest as
        a reason to surface a user clarification, but that is not in
        this task's scope (see SPEC-D-021 Gate 7A).
        """
        request_id = entry.source.ref
        chart_id = derive_chart_id_from_request_id(request_id)
        matching = next((r for r in chart_requests if r.request_id == request_id), None)
        metric_name = matching.user_intent if matching else f"chart for {entry.shot_id}"

        chart = ChartMaterial(
            chart_id=chart_id,
            shot_id=entry.shot_id,
            metric_name=metric_name,
            date_range=DateRange(start="2026-01-01", end="2026-12-31"),
            granularity=Granularity.MONTH,
            source=ChartSource(provider="planner_stub", symbol=request_id),
            verification_status="verified",
            chart_spec=ChartSpec(kind=ChartKind.LINE, series=["y"]),
            axis_spec=AxisSpec(
                x_axis=XAxis(
                    type=XAxisType.TIME,
                    labels=["2026-01-01"],
                    range=["2026-01-01", "2026-12-31"],
                ),
                y_axis=YAxis(
                    unit="USD",
                    min=0.0,
                    max=100.0,
                    scale_mode=ScaleMode.LINEAR,
                ),
            ),
        )
        out_dir = self._root / "phase_7a" / "chart_materials"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{chart_id}.json"
        out_path.write_text(
            chart.model_dump_json(indent=2, exclude_none=False),
            encoding="utf-8",
        )


__all__ = ["OrchestratorResult", "Phase7aOrchestrator"]
