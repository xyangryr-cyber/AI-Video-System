"""SPEC-A-108 (v3.18 D6): Requirements.platform becomes list[PlatformEntry]."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.shared.schemas.artifacts import PlatformEntry, Requirements


def _base_requirements_kwargs() -> dict:
    return dict(
        project_id="proj_x",
        title="t",
        topic="topic12345",
        duration_class="medium",
        target_duration={"min_sec": 480, "max_sec": 720},
        target_word_count={"min": 1000, "max": 2000},
        category={"level1": "金融", "level2": "宏观"},
        narrative_template="chronological",
        voice_preferences={"voice_id": "v1", "style": "calm"},
        subtitle_preferences={"style": "sentence", "highlight_enabled": True},
    )


def test_platformentry_role_constrained_to_primary_secondary():
    PlatformEntry(platform="bilibili", role="primary")
    PlatformEntry(platform="douyin", role="secondary")
    with pytest.raises(ValidationError):
        PlatformEntry(platform="x", role="tertiary")


def test_requirements_platform_must_be_list_of_platformentry():
    kwargs = _base_requirements_kwargs()
    kwargs["platform"] = [
        {"platform": "bilibili", "role": "primary"},
        {"platform": "douyin", "role": "secondary"},
    ]
    r = Requirements(**kwargs)
    assert len(r.platform) == 2
    assert r.platform[0].platform == "bilibili"
    assert r.platform[0].role == "primary"


def test_requirements_platform_rejects_string():
    kwargs = _base_requirements_kwargs()
    kwargs["platform"] = "youtube"
    with pytest.raises(ValidationError):
        Requirements(**kwargs)


def test_requirements_platform_requires_at_least_one_entry():
    kwargs = _base_requirements_kwargs()
    kwargs["platform"] = []
    with pytest.raises(ValidationError):
        Requirements(**kwargs)
