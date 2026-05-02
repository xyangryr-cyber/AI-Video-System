"""SPEC-A-112 (v3.18 D10): AssetSourcingEntry."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.shared.schemas.artifacts import AssetSourcingEntry


def test_asset_sourcing_entry_minimal():
    e = AssetSourcingEntry(shot_id="S1E1", status="not_needed")
    assert e.shot_id == "S1E1"
    assert e.status == "not_needed"
    assert e.need is None
    assert e.action is None
    assert e.data is None


def test_asset_sourcing_entry_full():
    e = AssetSourcingEntry(
        shot_id="S2E3",
        status="fetched",
        need="historical gold price chart",
        action="fetched from World Gold Council",
        data={"source_url": "https://gold.org/data.csv", "row_count": 24},
    )
    assert e.status == "fetched"
    assert e.data["row_count"] == 24


def test_asset_sourcing_entry_status_constrained():
    with pytest.raises(ValidationError):
        AssetSourcingEntry(shot_id="x", status="bogus")
