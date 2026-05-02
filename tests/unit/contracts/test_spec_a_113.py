"""SPEC-A-113 (v3.18 D11): KeyframeRenderEntry."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.shared.schemas.artifacts import KeyframeRenderEntry


def test_keyframe_render_entry_pending():
    e = KeyframeRenderEntry(shot_id="S1E1", render_status="pending_broll")
    assert e.file_name is None
    assert e.thumbnail_url is None


def test_keyframe_render_entry_rendered():
    e = KeyframeRenderEntry(
        shot_id="S2E1",
        render_status="rendered",
        file_name="keyframe_S2E1.png",
        thumbnail_url="https://cdn/thumb_S2E1.jpg",
    )
    assert e.file_name == "keyframe_S2E1.png"


def test_keyframe_render_status_constrained():
    with pytest.raises(ValidationError):
        KeyframeRenderEntry(shot_id="x", render_status="invalid")
