"""SPEC-A-110 (v3.18 D8): Candidate gains optional raw_bgm_url."""

from __future__ import annotations

from src.shared.schemas.candidate import Candidate


def test_candidate_accepts_raw_bgm_url():
    c = Candidate(
        candidate_id="cand_bgm_001",
        preview_url="https://cdn/preview.mp3",
        preview_type="audio",
        style_tags=["calm"],
        description="Calm corporate",
        is_recommended=True,
        adjustable_params={},
        rationale="matches narrative tempo",
        raw_bgm_url="https://cdn/raw.mp3",
    )
    assert c.raw_bgm_url == "https://cdn/raw.mp3"


def test_candidate_omits_raw_bgm_url_when_not_provided():
    c = Candidate(
        candidate_id="cand_x",
        preview_url="https://cdn/p.mp3",
        preview_type="audio",
        style_tags=[],
        description="x",
        is_recommended=False,
        adjustable_params={},
        rationale="x",
    )
    assert c.raw_bgm_url is None
