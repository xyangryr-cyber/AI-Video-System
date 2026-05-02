"""SPEC-A-114 (v3.18 D12): BRollEntry."""

from __future__ import annotations

from src.shared.schemas.artifacts import BRollEntry


def test_broll_entry_full():
    e = BRollEntry(
        file_name="broll_gold_bars.mp4",
        duration_sec=15.0,
        match_label="gold ingots, financial close-up",
        license="Pexels (CC0)",
        source_url="https://pexels.com/video/12345",
    )
    assert e.file_name == "broll_gold_bars.mp4"
    assert e.duration_sec == 15.0


def test_broll_entry_minimal_no_source_url():
    e = BRollEntry(
        file_name="broll_skyline.mp4",
        duration_sec=8.5,
        match_label="city skyline at dusk",
        license="Internal asset library",
    )
    assert e.source_url is None
