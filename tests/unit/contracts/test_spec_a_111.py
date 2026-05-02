"""SPEC-A-111 (v3.18 D9): AnnotationSpan."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.shared.schemas.artifacts import AnnotationSpan


def test_annotation_span_accepts_all_fields():
    s = AnnotationSpan(
        span_id="span_001",
        text_range=(120, 145),
        effect="emphasis",
        rationale="Highlight key data callout",
        narrative_role="data_callout",
    )
    assert s.span_id == "span_001"
    assert s.text_range == (120, 145)
    assert s.narrative_role == "data_callout"


def test_annotation_span_requires_narrative_role():
    with pytest.raises(ValidationError):
        AnnotationSpan(
            span_id="span_002",
            text_range=(0, 10),
            effect="pause",
            rationale="r",
        )
