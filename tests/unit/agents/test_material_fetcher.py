"""[SPEC-C-021] MaterialFetcher unit tests (AC-2).

Three source kinds (api / url / internal). Each verifies that (a) the
returned MaterialEntry has a fresh fetched_at and (b) the payload lands
under ``phase_7a/verified_materials/{material_id}.{ext}``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from src.backend.agents.material_fetcher import MaterialFetcher
from src.shared.schemas.material_manifest import (
    MaterialEntry,
    MaterialSource,
    MaterialType,
    RequiredLevel,
    SourceKind,
    VerificationStatus,
)


@pytest.fixture
def project_root(tmp_path: Path) -> Path:
    root = tmp_path / "proj_c021"
    (root / "phase_7a" / "verified_materials").mkdir(parents=True, exist_ok=True)
    (root / "phase_7a" / "chart_materials").mkdir(parents=True, exist_ok=True)
    return root


def _pending_entry(
    *,
    material_id: str,
    kind: SourceKind,
    ref: str,
) -> MaterialEntry:
    return MaterialEntry(
        material_id=material_id,
        shot_id="shot_01",
        material_type=MaterialType.FACT,
        required=RequiredLevel.HARD,
        source=MaterialSource(kind=kind, ref=ref),
        verification_status=VerificationStatus.PENDING,
        fetched_at="pending",
        rationale="for tests",
    )


class TestAC2FetchThreeKinds:
    def test_fetch_api(self, project_root: Path) -> None:
        entry = _pending_entry(
            material_id="mat_001", kind=SourceKind.API, ref="demo_symbol"
        )

        class ApiProvider:
            def fetch(self, ref: str) -> dict[str, Any]:
                return {"payload": b"{}", "ext": "json"}

        fetcher = MaterialFetcher(project_root=project_root, api_provider=ApiProvider())
        updated = fetcher.fetch(entry)

        assert updated.fetched_at and updated.fetched_at != "pending"
        out = project_root / "phase_7a" / "verified_materials" / "mat_001.json"
        assert out.exists()

    def test_fetch_url(self, project_root: Path) -> None:
        entry = _pending_entry(
            material_id="mat_002", kind=SourceKind.URL, ref="https://x/y.png"
        )

        class UrlProvider:
            def fetch(self, ref: str) -> dict[str, Any]:
                return {"payload": b"\x89PNGfake", "ext": "png"}

        fetcher = MaterialFetcher(project_root=project_root, url_provider=UrlProvider())
        updated = fetcher.fetch(entry)

        assert updated.fetched_at and updated.fetched_at != "pending"
        out = project_root / "phase_7a" / "verified_materials" / "mat_002.png"
        assert out.exists()
        assert out.read_bytes() == b"\x89PNGfake"

    def test_fetch_internal(self, project_root: Path, tmp_path: Path) -> None:
        src = tmp_path / "local_source.txt"
        src.write_bytes(b"internal-bytes")
        entry = _pending_entry(
            material_id="mat_003", kind=SourceKind.INTERNAL, ref=str(src)
        )

        fetcher = MaterialFetcher(project_root=project_root)
        updated = fetcher.fetch(entry)

        assert updated.fetched_at and updated.fetched_at != "pending"
        out = project_root / "phase_7a" / "verified_materials" / "mat_003.txt"
        assert out.exists()
        assert out.read_bytes() == b"internal-bytes"
