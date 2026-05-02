"""[SPEC-C-017] BgmCandidate -- P5 BGM candidate card schema.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-2.

Pre-v3.17, P5 emitted generic ``Candidate`` cards where ``preview_url``
pointed at the raw BGM file. v3.17 splits the P5 card into two URLs:

- ``preview_url``  -> ``phase_5/bgm_mix_preview_{candidate_id}.mp3``
  (narration+BGM mixed preview rendered by AudioMixPreviewService)
- ``raw_bgm_url``  -> ``phase_5/bgm_candidates/*.mp3``
  (the untouched BGM track; auxiliary listen)

Generic ``Candidate`` (candidate.py) stays untouched for the other four
candidate phases (P4/P7/P8/P9). This file is the P5-only specialization.

Backwards compatibility: legacy callers that still emit a single
``bgm_url`` field are accepted via a model_validator shim that emits a
``DeprecationWarning`` and promotes the value into ``preview_url`` +
``raw_bgm_url`` (mirroring pre-v3.17 semantics, where the raw BGM doubled
as the preview).
"""

from __future__ import annotations

import warnings
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BgmCandidate(_Strict):
    """Phase-5 BGM candidate card (v3.17 dual-URL shape)."""

    candidate_id: str = Field(pattern=r"^cand_[A-Za-z0-9_-]+$")
    preview_url: str = Field(min_length=1)
    preview_type: Literal["audio"] = "audio"
    raw_bgm_url: str = Field(min_length=1)
    style_tags: List[str]
    description: str = Field(min_length=1)
    is_recommended: bool
    adjustable_params: Dict[str, Any]
    rationale: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def _legacy_bgm_url_compat(cls, data: Any) -> Any:
        if not isinstance(data, dict) or "bgm_url" not in data:
            return data
        bgm_url = data.pop("bgm_url")
        warnings.warn(
            "BgmCandidate: field 'bgm_url' is deprecated; use "
            "'preview_url' (mix preview) + 'raw_bgm_url' (raw BGM) "
            "per SPEC-C-017.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not data.get("preview_url"):
            data["preview_url"] = bgm_url
        if not data.get("raw_bgm_url"):
            data["raw_bgm_url"] = bgm_url
        return data


__all__ = ["BgmCandidate"]
