"""Tests for [SPEC-A-103] StoryboardShotAnchor.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-4 (SPEC-0A.12).

Covers AC-3 (mandatory fields: anchor_text <= 200 chars + script_span_id +
start_char + end_char non-null) and AC-4 (downstream_bindings three fields
all optional). Re-exported by ``test_spec_a_103.py``.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
TS_PATH = REPO_ROOT / "src" / "shared" / "types" / "storyboard_shot_anchor.ts"


def _base_anchor(**overrides):
    payload = {
        "shot_id": "shot_01",
        "anchor_text": "黄金价格在过去五年呈上升趋势",
        "script_span_id": "seg_001",
        "start_char": 0,
        "end_char": 14,
        "downstream_bindings": {},
    }
    payload.update(overrides)
    return payload


class TestAC3StoryboardShotAnchorMandatoryFields:
    """AC-3: anchor_text <= 200 chars / script_span_id / start_char / end_char non-null."""

    def test_storyboard_shot_anchor_requires_anchor_text_within_200_chars_and_span_fields(
        self,
    ) -> None:
        from src.shared.schemas.storyboard_shot_anchor import (
            StoryboardShotAnchor,
        )

        # Baseline happy path.
        model = StoryboardShotAnchor(**_base_anchor())
        assert model.anchor_text == "黄金价格在过去五年呈上升趋势"
        assert model.script_span_id == "seg_001"
        assert model.start_char == 0
        assert model.end_char == 14

        # anchor_text exactly 200 chars = OK.
        StoryboardShotAnchor(**_base_anchor(anchor_text="a" * 200, end_char=200))

        # anchor_text 201 chars must be rejected.
        with pytest.raises(ValidationError):
            StoryboardShotAnchor(**_base_anchor(anchor_text="a" * 201, end_char=201))

        # anchor_text empty must be rejected (non-empty required).
        with pytest.raises(ValidationError):
            StoryboardShotAnchor(**_base_anchor(anchor_text=""))

        # script_span_id empty must be rejected.
        with pytest.raises(ValidationError):
            StoryboardShotAnchor(**_base_anchor(script_span_id=""))

        # script_span_id missing must be rejected.
        payload = _base_anchor()
        payload.pop("script_span_id")
        with pytest.raises(ValidationError):
            StoryboardShotAnchor(**payload)

        # start_char missing must be rejected.
        payload = _base_anchor()
        payload.pop("start_char")
        with pytest.raises(ValidationError):
            StoryboardShotAnchor(**payload)

        # end_char missing must be rejected.
        payload = _base_anchor()
        payload.pop("end_char")
        with pytest.raises(ValidationError):
            StoryboardShotAnchor(**payload)

        # start_char / end_char None rejected (they are mandatory ints).
        with pytest.raises(ValidationError):
            StoryboardShotAnchor(**_base_anchor(start_char=None))
        with pytest.raises(ValidationError):
            StoryboardShotAnchor(**_base_anchor(end_char=None))

        # Negative offsets rejected.
        with pytest.raises(ValidationError):
            StoryboardShotAnchor(**_base_anchor(start_char=-1, end_char=5))


class TestAC4DownstreamBindingsOptional:
    """AC-4: downstream_bindings three fields all optional."""

    def test_downstream_bindings_three_fields_are_optional(self) -> None:
        from src.shared.schemas.storyboard_shot_anchor import (
            DownstreamBindings,
            StoryboardShotAnchor,
        )

        expected_fields = {
            "p8_template_shot_id",
            "p9_broll_shot_id",
            "p10_track_ref",
        }
        assert set(DownstreamBindings.model_fields.keys()) == expected_fields

        # All three fields carry `None` as default (optional).
        for name in expected_fields:
            field = DownstreamBindings.model_fields[name]
            assert not field.is_required(), (
                f"DownstreamBindings.{name} must be optional (has no default)"
            )

        # Empty object parses — all three optional.
        empty = DownstreamBindings()
        for name in expected_fields:
            assert getattr(empty, name) is None

        # Partial set parses (e.g. only p9_broll_shot_id).
        partial = DownstreamBindings(p9_broll_shot_id="broll_shot_07")
        assert partial.p9_broll_shot_id == "broll_shot_07"
        assert partial.p8_template_shot_id is None
        assert partial.p10_track_ref is None

        # All three set parses.
        full = DownstreamBindings(
            p8_template_shot_id="tpl_01",
            p9_broll_shot_id="broll_shot_07",
            p10_track_ref="track_a",
        )
        assert full.p8_template_shot_id == "tpl_01"

        # A StoryboardShotAnchor with empty downstream_bindings is valid.
        anchor = StoryboardShotAnchor(**_base_anchor())
        assert anchor.downstream_bindings.p8_template_shot_id is None

    def test_ts_mirror_marks_downstream_bindings_fields_optional(self) -> None:
        assert TS_PATH.exists(), f"missing TS file: {TS_PATH}"
        src = TS_PATH.read_text(encoding="utf-8")
        m = re.search(
            r"export\s+interface\s+DownstreamBindings\s*\{([^{}]+)\}",
            src,
        )
        assert m, "DownstreamBindings interface not found in storyboard_shot_anchor.ts"
        body = m.group(1)
        # Each of the 3 fields must use `?:` (optional) syntax in TS.
        for name in (
            "p8_template_shot_id",
            "p9_broll_shot_id",
            "p10_track_ref",
        ):
            assert re.search(rf"\b{name}\?\s*:\s*string", body), (
                f"DownstreamBindings.{name} must be optional (field?: string) in TS"
            )
