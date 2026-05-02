"""[SPEC-C-021] Phase-7A orchestration integration tests.

Covers:
  * AC-4 — P7 PASS -> planner -> fan-out fetch -> fan-out verify ->
    all terminal -> FSM advances from P7A to P8 entry.
  * AC-5 — transient 5xx exhausted -> single material terminates in
    ``missing``; sibling materials still reach ``verified``; retry count
    matches max_attempts from SPEC-B-015.
  * AC-7 — chart-type materials produce a ChartMaterial JSON side-file
    under ``phase_7a/chart_materials/chart_*.json``.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from src.backend.agents.material_fetcher import MaterialFetcher
from src.backend.agents.material_verifier import MaterialVerifier
from src.backend.agents.storyboard_asset_planner import StoryboardAssetPlanner
from src.backend.engine.phase_7a_orchestrator import Phase7aOrchestrator
from src.backend.workers.p7a_tasks import TransientProviderError
from src.shared.schemas.chart_material import ChartMaterial
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


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    root = tmp_path / "proj_c021"
    (root / "phase_7a" / "verified_materials").mkdir(parents=True, exist_ok=True)
    (root / "phase_7a" / "chart_materials").mkdir(parents=True, exist_ok=True)
    return root


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
    ref: str,
    kind: SourceKind = SourceKind.API,
) -> MaterialEntry:
    return MaterialEntry(
        material_id=material_id,
        shot_id=shot_id,
        material_type=MaterialType.FACT,
        required=RequiredLevel.HARD,
        source=MaterialSource(kind=kind, ref=ref),
        verification_status=VerificationStatus.PENDING,
        fetched_at="pending",
        rationale="for tests",
    )


class ApiProvider:
    def fetch(self, ref: str) -> dict[str, Any]:
        return {"payload": b'{"rows":[]}', "ext": "json"}


class PassingFact:
    def check(self, entry: MaterialEntry, path: Path) -> tuple[bool, str]:
        return True, ""


# -----------------------------------------------------------------------
# AC-4: full chain
# -----------------------------------------------------------------------


class TestAC4FullChain:
    def test_p7_pass_to_p8_full_chain(self, project_root: Path) -> None:
        shots = [_anchor("shot_01")]
        charts = [_chart_request("req_001")]

        fetcher = MaterialFetcher(project_root=project_root, api_provider=ApiProvider())
        verifier = MaterialVerifier(
            project_root=project_root, fact_checker=PassingFact()
        )
        orchestrator = Phase7aOrchestrator(
            project_id="proj_001",
            project_root=project_root,
            planner=StoryboardAssetPlanner,
            fetcher=fetcher,
            verifier=verifier,
        )
        result = orchestrator.run(shots=shots, chart_requests=charts)

        assert result.advanced_to_p8 is True
        manifest_path = project_root / "phase_7a" / "material_manifest.json"
        assert manifest_path.exists()
        manifest = MaterialManifest.model_validate_json(manifest_path.read_text())
        # Every material reached a terminal state.
        assert all(
            m.verification_status
            in {
                VerificationStatus.VERIFIED,
                VerificationStatus.REJECTED,
                VerificationStatus.MISSING,
            }
            for m in manifest.materials
        )


# -----------------------------------------------------------------------
# AC-5: retry -> missing + sibling isolation
# -----------------------------------------------------------------------


class TestAC5RetryIsolation:
    def test_fetch_retry_to_missing_isolates(self, project_root: Path) -> None:
        shots = [_anchor("shot_01"), _anchor("shot_02")]
        manifest = MaterialManifest(
            project_id="proj_001",
            phase="7A",
            materials=[
                _pending_entry(material_id="mat_901", shot_id="shot_01", ref="flaky"),
                _pending_entry(material_id="mat_902", shot_id="shot_02", ref="good"),
            ],
        )

        call_counts: dict[str, int] = {"flaky": 0, "good": 0}

        class FlakyProvider:
            def fetch(self, ref: str) -> dict[str, Any]:
                call_counts[ref] += 1
                if ref == "flaky":
                    raise TransientProviderError("boom", status_code=503)
                return {"payload": b"ok-bytes", "ext": "json"}

        fetcher = MaterialFetcher(
            project_root=project_root, api_provider=FlakyProvider()
        )
        verifier = MaterialVerifier(
            project_root=project_root, fact_checker=PassingFact()
        )
        orchestrator = Phase7aOrchestrator(
            project_id="proj_001",
            project_root=project_root,
            planner=StoryboardAssetPlanner,
            fetcher=fetcher,
            verifier=verifier,
        )
        result = orchestrator.run_with_manifest(manifest=manifest, shots=shots)

        by_id = {m.material_id: m for m in result.manifest.materials}
        assert by_id["mat_901"].verification_status == VerificationStatus.MISSING
        assert by_id["mat_902"].verification_status == VerificationStatus.VERIFIED
        assert call_counts["flaky"] == 3  # SPEC-B-015 max_attempts


# -----------------------------------------------------------------------
# AC-7: chart-type materials emit ChartMaterial JSON
# -----------------------------------------------------------------------


class TestAC7ChartMaterialEmitted:
    def test_chart_material_emitted_alongside(self, project_root: Path) -> None:
        shots = [_anchor("shot_01")]
        charts = [_chart_request("req_007")]

        fetcher = MaterialFetcher(project_root=project_root, api_provider=ApiProvider())
        verifier = MaterialVerifier(
            project_root=project_root, fact_checker=PassingFact()
        )
        orchestrator = Phase7aOrchestrator(
            project_id="proj_001",
            project_root=project_root,
            planner=StoryboardAssetPlanner,
            fetcher=fetcher,
            verifier=verifier,
        )
        orchestrator.run(shots=shots, chart_requests=charts)

        chart_dir = project_root / "phase_7a" / "chart_materials"
        files = list(chart_dir.glob("chart_*.json"))
        assert files, "expected >=1 chart_*.json under phase_7a/chart_materials/"
        for f in files:
            data = json.loads(f.read_text(encoding="utf-8"))
            ChartMaterial.model_validate(data)
