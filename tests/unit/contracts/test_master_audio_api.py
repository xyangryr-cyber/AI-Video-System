"""Tests for [SPEC-A-017] GET /artifacts/master_audio endpoint contracts.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-5.

Covers AC-1 (route + query param enum), AC-2 (response field parity with
MasterAudioArtifact), AC-3 (error codes invalid_phase=400 + master_not_ready=404).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError as PydanticError

ROOT = Path(__file__).resolve().parents[3]
API_ROUTES_TS = ROOT / "src" / "shared" / "types" / "api_routes.ts"
API_MASTER_AUDIO_TS = ROOT / "src" / "shared" / "types" / "api_master_audio.ts"


ROUTE_PATH = "/api/projects/{project_id}/artifacts/master_audio"


class TestAC1RouteDefinition:
    """AC-1: Route + query-param enum."""

    def test_route_definition_present(self):
        assert API_ROUTES_TS.exists(), (
            f"{API_ROUTES_TS.name} must exist (SPEC-A-017 allowed_files)"
        )
        ts_src = API_ROUTES_TS.read_text(encoding="utf-8")
        assert ROUTE_PATH in ts_src, f"api_routes.ts missing route path {ROUTE_PATH!r}"
        # Method + path must co-reside in the same route object; allow any
        # whitespace/newlines between them (re.DOTALL so `.` crosses lines).
        assert re.search(
            r"(['\"])GET\1[\s\S]{0,400}artifacts/master_audio",
            ts_src,
        ), "api_routes.ts must declare the master_audio endpoint as GET"

    def test_query_param_phase_enum(self):
        """Pydantic Request model must constrain phase to Literal[4, 5, 6]."""
        from src.shared.schemas.api_master_audio import GetMasterAudioRequest

        # Valid phases
        for phase in (4, 5, 6):
            req = GetMasterAudioRequest(phase=phase)
            assert req.phase == phase

        # Invalid phases must be rejected at the contract boundary
        for bad in (0, 3, 7, 11):
            with pytest.raises(PydanticError):
                GetMasterAudioRequest(phase=bad)

    def test_ts_mirror_phase_enum(self):
        """TS Request type must mirror the Literal[4, 5, 6] constraint."""
        ts_src = API_MASTER_AUDIO_TS.read_text(encoding="utf-8")
        assert re.search(r"\b4\s*\|\s*5\s*\|\s*6\b", ts_src), (
            "api_master_audio.ts must type `phase` as `4 | 5 | 6`"
        )


class TestAC2ResponseFieldsMatchMasterAudioArtifact:
    """AC-2: Response fields: master_audio_url / download_url / based_on_phase /
    kind / checksum / version; aligned with A-013 MasterAudioArtifact."""

    REQUIRED_RESPONSE_FIELDS = {
        "master_audio_url",
        "download_url",
        "based_on_phase",
        "kind",
        "checksum",
        "version",
    }

    def test_response_fields_match_master_audio_artifact(self):
        from src.shared.schemas.api_master_audio import GetMasterAudioResponse

        declared = set(GetMasterAudioResponse.model_fields.keys())
        missing = self.REQUIRED_RESPONSE_FIELDS - declared
        assert not missing, f"GetMasterAudioResponse missing fields: {sorted(missing)}"

    def test_response_kind_aligns_with_master_audio_artifact(self):
        """AC-2: `kind` must accept the three MasterAudioArtifact discriminator
        values and nothing else."""
        from src.shared.schemas.api_master_audio import GetMasterAudioResponse

        valid_kinds = ("narration_master", "bgm_mix_master", "final_audio_master")
        for kind, phase in zip(valid_kinds, (4, 5, 6)):
            resp = GetMasterAudioResponse(
                master_audio_url=f"/api/files/phase_{phase}/{kind}.mp3",
                download_url=f"/api/files/phase_{phase}/{kind}.mp3?download=1",
                based_on_phase=phase,
                kind=kind,
                checksum="sha256:" + "a" * 64,
                version=1,
            )
            assert resp.kind == kind
            assert resp.based_on_phase == phase

        # Invalid kind rejected
        with pytest.raises(PydanticError):
            GetMasterAudioResponse(
                master_audio_url="/x",
                download_url="/x",
                based_on_phase=4,
                kind="totally_bogus",
                checksum="sha256:" + "a" * 64,
                version=1,
            )

    def test_response_based_on_phase_only_456(self):
        from src.shared.schemas.api_master_audio import GetMasterAudioResponse

        for bad in (0, 3, 7, 11):
            with pytest.raises(PydanticError):
                GetMasterAudioResponse(
                    master_audio_url="/x",
                    download_url="/x",
                    based_on_phase=bad,
                    kind="narration_master",
                    checksum="sha256:" + "a" * 64,
                    version=1,
                )

    def test_ts_mirror_has_every_response_field(self):
        ts_src = API_MASTER_AUDIO_TS.read_text(encoding="utf-8")
        for field in self.REQUIRED_RESPONSE_FIELDS:
            assert re.search(rf"\b{re.escape(field)}\b", ts_src), (
                f"api_master_audio.ts missing response field {field!r}"
            )


class TestAC3ErrorCodes:
    """AC-3: phase ∉ [4,5,6] → 400 invalid_phase；master 未就绪 → 404 master_not_ready."""

    def test_invalid_phase_returns_400(self):
        from src.shared.schemas.api_master_audio import (
            MASTER_AUDIO_ERROR_HTTP_STATUS,
            MasterAudioErrorCode,
        )

        assert MasterAudioErrorCode.INVALID_PHASE.value == "invalid_phase"
        assert MASTER_AUDIO_ERROR_HTTP_STATUS[MasterAudioErrorCode.INVALID_PHASE] == 400

    def test_master_not_ready_returns_404(self):
        from src.shared.schemas.api_master_audio import (
            MASTER_AUDIO_ERROR_HTTP_STATUS,
            MasterAudioErrorCode,
        )

        assert MasterAudioErrorCode.MASTER_NOT_READY.value == "master_not_ready"
        assert (
            MASTER_AUDIO_ERROR_HTTP_STATUS[MasterAudioErrorCode.MASTER_NOT_READY] == 404
        )

    def test_ts_mirror_declares_both_error_codes(self):
        ts_src = API_MASTER_AUDIO_TS.read_text(encoding="utf-8")
        for code in ("invalid_phase", "master_not_ready"):
            assert re.search(rf"['\"]{re.escape(code)}['\"]", ts_src), (
                f"api_master_audio.ts missing error code {code!r}"
            )
