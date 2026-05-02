"""SPEC-A-107 (v3.18 D5): KeyDataPoint gains optional usage + link."""

from __future__ import annotations

from src.shared.schemas.shared_types import KeyDataPoint


def test_keydatapoint_accepts_usage_and_link():
    kdp = KeyDataPoint(
        data_point_id="dp_gold_2024",
        label="2024 Gold Price",
        value=2650.5,
        unit="USD/oz",
        source="World Gold Council",
        trust_level="source_verified",
        segment_id="seg_001",
        usage="S2E1 / P4 / P6",
        link="https://www.gold.org/",
    )
    assert kdp.usage == "S2E1 / P4 / P6"
    assert kdp.link == "https://www.gold.org/"


def test_keydatapoint_omits_usage_and_link_when_not_provided():
    kdp = KeyDataPoint(
        data_point_id="dp_x",
        label="x",
        value=1,
        unit="",
        source="src",
        trust_level="llm_generated",
        segment_id="seg_002",
    )
    assert kdp.usage is None
    assert kdp.link is None
