"""Tests for [SPEC-A-016] ChartMaterial schema (+ axis_spec sub-schema).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-4.

Covers AC-1..AC-6 from tasks/SPEC-A/A-016-chart-material-schema.md.

Precedent (A-015 PROGRESS decisions): the task card's `Allowed Files`
lists this file (`tests/unit/contracts/test_chart_material_schema.py`)
while its `Verification Commands` / `Test Mapping` reference
`tests/unit/contracts/test_spec_a_016.py`. Substantive AC bodies live
here (allowed path); the skip-stub at `test_spec_a_016.py` is kept
untouched (outside allowed_files).
"""

from __future__ import annotations

import json
import random
import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict

import pytest
from jsonschema import Draft202012Validator
from jsonschema import ValidationError as JsonSchemaError
from pydantic import ValidationError as PydanticError

ROOT = Path(__file__).resolve().parents[3]
SCHEMA_PATH = ROOT / "schemas" / "chart_material.schema.json"
TS_PATH = ROOT / "src" / "shared" / "types" / "chart_material.ts"


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _chart_material_payload(**overrides: Any) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chart_id": "chart_001",
        "shot_id": "shot_01",
        "metric_name": "gold_price_usd_per_oz",
        "date_range": {"start": "2024-01-01", "end": "2024-01-07"},
        "granularity": "day",
        "source": {"provider": "wind", "symbol": "XAU"},
        "verification_status": "verified",
        "chart_spec": {
            "kind": "line",
            "series": [
                {"name": "gold", "data": [2000, 2010, 2020, 2015, 2025, 2030, 2035]}
            ],
        },
        "axis_spec": {
            "x_axis": {
                "type": "time",
                "labels": [
                    "2024-01-01",
                    "2024-01-02",
                    "2024-01-03",
                    "2024-01-04",
                    "2024-01-05",
                    "2024-01-06",
                    "2024-01-07",
                ],
                "range": ["2024-01-01", "2024-01-07"],
            },
            "y_axis": {
                "unit": "USD/oz",
                "min": 1990.0,
                "max": 2050.0,
                "scale_mode": "linear",
            },
        },
    }
    payload.update(overrides)
    return payload


# ---------------------------------------------------------------------------
# AC-1: JSON Schema accepts legal payloads and rejects illegal ones.
# ---------------------------------------------------------------------------


class TestAC1:
    def test_valid(self):
        validator = Draft202012Validator(_load_schema())
        validator.validate(_chart_material_payload())

    def test_invalid_y_axis_min_gt_max(self):
        """y_axis.min < max is expressed as a program check (JSON Schema
        cannot express cross-field inequality). Pydantic enforces it."""
        from src.shared.schemas.chart_material import ChartMaterial

        bad = _chart_material_payload()
        bad["axis_spec"]["y_axis"]["min"] = 2100.0
        bad["axis_spec"]["y_axis"]["max"] = 2000.0
        with pytest.raises(PydanticError):
            ChartMaterial.model_validate(bad)

    def test_y_axis_min_equal_max_rejected(self):
        from src.shared.schemas.chart_material import ChartMaterial

        bad = _chart_material_payload()
        bad["axis_spec"]["y_axis"]["min"] = 2000.0
        bad["axis_spec"]["y_axis"]["max"] = 2000.0
        with pytest.raises(PydanticError):
            ChartMaterial.model_validate(bad)

    def test_x_axis_range_length(self):
        validator = Draft202012Validator(_load_schema())
        bad = _chart_material_payload()
        bad["axis_spec"]["x_axis"]["range"] = ["2024-01-01"]
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)
        bad["axis_spec"]["x_axis"]["range"] = [
            "2024-01-01",
            "2024-01-02",
            "2024-01-03",
        ]
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_verification_status_must_be_verified(self):
        validator = Draft202012Validator(_load_schema())
        for bad_status in ("pending", "rejected", "missing", "verifieD", ""):
            bad = _chart_material_payload()
            bad["verification_status"] = bad_status
            with pytest.raises(JsonSchemaError):
                validator.validate(bad)
        # Positive case: must accept exactly "verified".
        validator.validate(_chart_material_payload())

    def test_invalid_chart_id_pattern(self):
        validator = Draft202012Validator(_load_schema())
        for bad_id in ("chart_1", "chart_12", "cht_001", "1234", ""):
            bad = _chart_material_payload(chart_id=bad_id)
            with pytest.raises(JsonSchemaError):
                validator.validate(bad)

    def test_invalid_shot_id_pattern(self):
        validator = Draft202012Validator(_load_schema())
        bad = _chart_material_payload(shot_id="shot_1")
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_invalid_granularity(self):
        validator = Draft202012Validator(_load_schema())
        bad = _chart_material_payload(granularity="year")
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_invalid_chart_spec_kind(self):
        validator = Draft202012Validator(_load_schema())
        bad = _chart_material_payload()
        bad["chart_spec"]["kind"] = "candlestick"
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_invalid_scale_mode(self):
        validator = Draft202012Validator(_load_schema())
        bad = _chart_material_payload()
        bad["axis_spec"]["y_axis"]["scale_mode"] = "sqrt"
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_invalid_x_axis_type(self):
        validator = Draft202012Validator(_load_schema())
        bad = _chart_material_payload()
        bad["axis_spec"]["x_axis"]["type"] = "log"
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)

    def test_missing_required_top_level(self):
        validator = Draft202012Validator(_load_schema())
        for missing in (
            "chart_id",
            "shot_id",
            "metric_name",
            "date_range",
            "granularity",
            "source",
            "verification_status",
            "chart_spec",
            "axis_spec",
        ):
            bad = _chart_material_payload()
            bad.pop(missing)
            with pytest.raises(JsonSchemaError):
                validator.validate(bad)

    def test_empty_series_rejected(self):
        validator = Draft202012Validator(_load_schema())
        bad = _chart_material_payload()
        bad["chart_spec"]["series"] = []
        with pytest.raises(JsonSchemaError):
            validator.validate(bad)


# ---------------------------------------------------------------------------
# AC-2: Pydantic <-> TS mirror.
# ---------------------------------------------------------------------------


def _ts_fields(ts_path: Path, interface_name: str) -> set[str]:
    text = ts_path.read_text(encoding="utf-8")
    header = re.search(
        rf"export interface {re.escape(interface_name)}\s*\{{",
        text,
    )
    assert header, f"interface {interface_name} not found in {ts_path.name}"
    start = header.end()
    depth = 1
    i = start
    in_line_comment = False
    while i < len(text) and depth > 0:
        ch = text[i]
        if in_line_comment:
            if ch == "\n":
                in_line_comment = False
        elif ch == "/" and i + 1 < len(text) and text[i + 1] == "/":
            in_line_comment = True
            i += 1
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        i += 1
    body = text[start : i - 1]
    cleaned: list[str] = []
    for raw in body.splitlines():
        idx = raw.find("//")
        cleaned.append(raw[:idx] if idx >= 0 else raw)
    body = "\n".join(cleaned)
    fields: set[str] = set()
    for logical in body.split(";"):
        logical = logical.strip()
        if not logical:
            continue
        simplified = re.sub(r"\{[^{}]*\}", "", logical, flags=re.DOTALL)
        m = re.match(r"([A-Za-z_][A-Za-z0-9_]*)\??:", simplified)
        if m:
            fields.add(m.group(1))
    return fields


class TestAC2:
    def test_pydantic_ts_alignment(self):
        from src.shared.schemas.chart_material import (
            AxisSpec,
            ChartMaterial,
            ChartSource,
            ChartSpec,
            DateRange,
            XAxis,
            YAxis,
        )

        assert set(ChartMaterial.model_fields) == _ts_fields(TS_PATH, "ChartMaterial")
        assert set(DateRange.model_fields) == _ts_fields(TS_PATH, "DateRange")
        assert set(ChartSource.model_fields) == _ts_fields(TS_PATH, "ChartSource")
        assert set(ChartSpec.model_fields) == _ts_fields(TS_PATH, "ChartSpec")
        assert set(AxisSpec.model_fields) == _ts_fields(TS_PATH, "AxisSpec")
        assert set(XAxis.model_fields) == _ts_fields(TS_PATH, "XAxis")
        assert set(YAxis.model_fields) == _ts_fields(TS_PATH, "YAxis")


# ---------------------------------------------------------------------------
# AC-3: chart_id <-> request_id 1:1 derivation (ChartRequest not redefined).
# ---------------------------------------------------------------------------


class TestAC3:
    def test_chart_id_derived_from_request_id(self):
        from src.shared.schemas.chart_material import (
            derive_chart_id_from_request_id,
            derive_request_id_from_chart_id,
        )

        # Forward rule: request_id -> chart_id.
        assert derive_chart_id_from_request_id("req_001") == "chart_001"
        assert derive_chart_id_from_request_id("req_42042") == "chart_42042"

        # Reverse rule: chart_id -> request_id. Bijection.
        assert derive_request_id_from_chart_id("chart_001") == "req_001"
        assert derive_request_id_from_chart_id("chart_42042") == "req_42042"

        # Round-trip: any valid request_id -> chart_id -> back to itself.
        for rid in ("req_001", "req_123", "req_999999"):
            assert (
                derive_request_id_from_chart_id(derive_chart_id_from_request_id(rid))
                == rid
            )

        # Invalid inputs raise.
        for bad_req in ("request_001", "req_1", "req_", "", "chart_001"):
            with pytest.raises(ValueError):
                derive_chart_id_from_request_id(bad_req)
        for bad_chart in ("chart_1", "chart_", "", "req_001"):
            with pytest.raises(ValueError):
                derive_request_id_from_chart_id(bad_chart)


# ---------------------------------------------------------------------------
# AC-4: property-based-in-spirit sweep — random date_range + granularity
# implies axis_spec.x_axis.labels count matches granularity (+/- 1 tolerance).
#
# Note: `hypothesis` is not in `requirements-dev.txt`; HARNESS §7.2 forbids
# unmanaged `pip install`. The sweep uses `random.Random(seed)` so the
# "property" (generator -> invariant) is still exercised deterministically
# and reproducibly across 60 cases covering day/week/month x several range
# sizes (>= 6 distinct shapes per granularity).
# ---------------------------------------------------------------------------


class TestAC4:
    def test_property_based_axis_labels(self):
        from src.shared.schemas.chart_material import build_axis_x_labels

        rng = random.Random(20260420)
        for _ in range(60):
            granularity = rng.choice(("day", "week", "month"))
            start = date(2024, 1, 1) + timedelta(days=rng.randint(0, 400))
            span_days = rng.randint(1, 365)
            end = start + timedelta(days=span_days)

            labels = build_axis_x_labels(
                start.isoformat(), end.isoformat(), granularity
            )

            if granularity == "day":
                expected = (end - start).days + 1
            elif granularity == "week":
                expected = ((end - start).days // 7) + 1
            else:  # month
                expected = (
                    (end.year - start.year) * 12 + (end.month - start.month)
                ) + 1

            assert abs(len(labels) - expected) <= 1, (
                f"granularity={granularity} start={start} end={end} "
                f"got {len(labels)} labels, expected ~{expected}"
            )

        # Plus six hand-picked shapes that anchor the property for humans.
        canonical = [
            ("2024-01-01", "2024-01-07", "day", 7),
            ("2024-01-01", "2024-02-29", "day", 60),
            ("2024-01-01", "2024-01-28", "week", 4),
            ("2024-01-01", "2024-03-31", "week", 13),
            ("2024-01-01", "2024-06-30", "month", 6),
            ("2024-01-01", "2024-12-31", "month", 12),
        ]
        for s, e, g, exp in canonical:
            got = len(build_axis_x_labels(s, e, g))
            assert abs(got - exp) <= 1, f"{s}..{e} @ {g} -> {got} != {exp}+-1"


# ---------------------------------------------------------------------------
# AC-5: artifact registry carries the new chart_material entry.
# ---------------------------------------------------------------------------


class TestAC5:
    def test_registry_contains_chart_material_entry(self):
        from src.shared.schemas.artifact_registry import ARTIFACT_REGISTRY

        key = "phase_7a/chart_materials/chart_*.json"
        assert key in ARTIFACT_REGISTRY
        entry = ARTIFACT_REGISTRY[key]
        assert "StoryboardAssetPlanner" in entry.producer
        assert "FinancialDataService" in entry.producer
        assert any("KeyframeRenderAgent" in c for c in entry.consumers)
        assert "chart_material.schema.json" in entry.validation
        assert "axis_spec" in entry.validation


# ---------------------------------------------------------------------------
# AC-6: L1 chart <-> axis consistency. line kind requires x_axis.type in
# {time, value} (category is illegal for line); bar allows category.
# ---------------------------------------------------------------------------


class TestAC6:
    def test_l1_chart_axis_consistency_violation(self):
        from src.shared.schemas.chart_material import (
            ChartMaterial,
            ChartAxisConsistencyError,
            validate_chart_axis_consistency,
        )

        payload = _chart_material_payload()
        payload["chart_spec"]["kind"] = "line"
        payload["axis_spec"]["x_axis"]["type"] = "category"
        # Labels need to be non-empty strings in category mode.
        payload["axis_spec"]["x_axis"]["labels"] = ["Q1", "Q2"]
        payload["axis_spec"]["x_axis"]["range"] = ["Q1", "Q2"]

        # Pydantic still parses (kind/type individually valid); the
        # cross-field violation is detected by the dedicated L1 check.
        material = ChartMaterial.model_validate(payload)
        with pytest.raises(ChartAxisConsistencyError):
            validate_chart_axis_consistency(material)

    def test_l1_chart_axis_consistency_line_time_ok(self):
        from src.shared.schemas.chart_material import (
            ChartMaterial,
            validate_chart_axis_consistency,
        )

        material = ChartMaterial.model_validate(_chart_material_payload())
        validate_chart_axis_consistency(material)  # no raise

    def test_l1_chart_axis_consistency_bar_category_ok(self):
        from src.shared.schemas.chart_material import (
            ChartMaterial,
            validate_chart_axis_consistency,
        )

        payload = _chart_material_payload()
        payload["chart_spec"]["kind"] = "bar"
        payload["axis_spec"]["x_axis"]["type"] = "category"
        payload["axis_spec"]["x_axis"]["labels"] = ["Q1", "Q2", "Q3", "Q4"]
        payload["axis_spec"]["x_axis"]["range"] = ["Q1", "Q4"]
        material = ChartMaterial.model_validate(payload)
        validate_chart_axis_consistency(material)  # no raise


# ---------------------------------------------------------------------------
# Extra: Pydantic strictness gate.
# ---------------------------------------------------------------------------


class TestPydanticStrictness:
    def test_rejects_unknown_fields(self):
        from src.shared.schemas.chart_material import ChartMaterial

        payload = _chart_material_payload()
        payload["extra_field"] = "nope"
        with pytest.raises(PydanticError):
            ChartMaterial.model_validate(payload)

    def test_rejects_non_verified(self):
        from src.shared.schemas.chart_material import ChartMaterial

        bad = _chart_material_payload()
        bad["verification_status"] = "pending"
        with pytest.raises(PydanticError):
            ChartMaterial.model_validate(bad)

    def test_rejects_x_axis_range_wrong_length(self):
        from src.shared.schemas.chart_material import ChartMaterial

        bad = _chart_material_payload()
        bad["axis_spec"]["x_axis"]["range"] = ["2024-01-01"]
        with pytest.raises(PydanticError):
            ChartMaterial.model_validate(bad)
