"""[SPEC-A-017] GET /artifacts/master_audio endpoint contracts (Pydantic).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-5.

Endpoint:
  GET /api/projects/{project_id}/artifacts/master_audio?phase={4|5|6}

Response fields are aligned with A-013 `MasterAudioArtifact` (kind /
based_on_phase / checksum / version) plus the two URL fields the API layer
derives (master_audio_url / download_url).

Error contract:
  - phase ∉ [4,5,6]            → 400 `invalid_phase`
  - master-audio not produced  → 404 `master_not_ready`

Keep in lockstep with `src/shared/types/api_master_audio.ts`.
"""

from __future__ import annotations

from enum import Enum
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

_CHECKSUM_RE = r"^sha256:[a-f0-9]{64}$"


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class GetMasterAudioRequest(_Strict):
    """Query params for GET /artifacts/master_audio."""

    phase: Literal[4, 5, 6]


MasterAudioKind = Literal["narration_master", "bgm_mix_master", "final_audio_master"]


class GetMasterAudioResponse(_Strict):
    """Response body for GET /artifacts/master_audio."""

    master_audio_url: str = Field(min_length=1)
    download_url: str = Field(min_length=1)
    based_on_phase: Literal[4, 5, 6]
    kind: MasterAudioKind
    checksum: str = Field(pattern=_CHECKSUM_RE)
    version: int = Field(ge=1)


class MasterAudioErrorCode(str, Enum):
    """Error codes specific to this endpoint (SPEC-A-017 §AC-3)."""

    INVALID_PHASE = "invalid_phase"
    MASTER_NOT_READY = "master_not_ready"


MASTER_AUDIO_ERROR_HTTP_STATUS: Final[dict[MasterAudioErrorCode, int]] = {
    MasterAudioErrorCode.INVALID_PHASE: 400,
    MasterAudioErrorCode.MASTER_NOT_READY: 404,
}


__all__ = [
    "GetMasterAudioRequest",
    "GetMasterAudioResponse",
    "MASTER_AUDIO_ERROR_HTTP_STATUS",
    "MasterAudioErrorCode",
    "MasterAudioKind",
]
