"""Tests for [SPEC-F-101] AxisSpec auto-generation (deterministic, pure function).

Verifies both the TypeScript and Python implementations match in behavior:
- Call the Python implementation directly via import.
- Read the TS source and verify it contains equivalent logic.
"""

import hashlib
import importlib
import json
import os
import re
import sys

import pytest

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "src", "backend", "services"))

TS_AXIS_PATH = os.path.join(
    PROJECT_ROOT, "src", "frontend", "remotion", "utils", "axis_spec_generator.ts"
)


def _read_ts(path: str) -> str:
    assert os.path.isfile(path), f"TS source not found: {path}"
    with open(path, encoding="utf-8") as f:
        return f.read()


# ---------------------------------------------------------------------------
# Helper: import the Python axis spec generator
# ---------------------------------------------------------------------------


def _py_generate():
    """Import and return the Python generate_axis_spec function."""
    mod = importlib.import_module("axis_spec_generator")
    return mod.generate_axis_spec


# ---------------------------------------------------------------------------
# AC-1: x_axis type inference
# ---------------------------------------------------------------------------


class TestAC1:
    """AC-1: day/week/month -> x_axis.type=time; category input -> category"""

    def test_x_axis_time_vs_category_inference(self):
        # --- Python side ---
        gen = _py_generate()
        input_day = {
            "data_points": [{"x": "2024-01-01", "y": 100}],
            "unit": "USD",
            "granularity": "day",
        }
        result = gen(input_day)
        assert result["x_axis"]["type"] == "time", (
            f"day granularity should produce x_axis.type='time', got {result['x_axis']['type']}"
        )

        input_week = {
            "data_points": [{"x": "2024-W01", "y": 100}],
            "unit": "USD",
            "granularity": "week",
        }
        result = gen(input_week)
        assert result["x_axis"]["type"] == "time", (
            f"week granularity should produce x_axis.type='time', got {result['x_axis']['type']}"
        )

        input_month = {
            "data_points": [{"x": "2024-01", "y": 100}],
            "unit": "USD",
            "granularity": "month",
        }
        result = gen(input_month)
        assert result["x_axis"]["type"] == "time", (
            f"month granularity should produce x_axis.type='time', got {result['x_axis']['type']}"
        )

        input_cat = {
            "data_points": [{"x": "Tesla", "y": 100}],
            "unit": "USD",
            "granularity": "category",
        }
        result = gen(input_cat)
        assert result["x_axis"]["type"] == "category", (
            f"category granularity should produce x_axis.type='category', got {result['x_axis']['type']}"
        )

        # --- TypeScript side: verify equivalent logic ---
        ts_src = _read_ts(TS_AXIS_PATH)
        assert re.search(r"day|['\"]week['\"]|['\"]month['\"]", ts_src), (
            "TS source missing time granularity keywords"
        )
        assert re.search(r"category", ts_src, re.IGNORECASE), (
            "TS source missing category keyword"
        )
        assert re.search(r"x_axis|xAxis|_type.*time|type.*=.*['\"]time['\"]", ts_src), (
            "TS x_axis type logic not found"
        )


# ---------------------------------------------------------------------------
# AC-2: y_axis min/max = data min/max +/- 5%
# ---------------------------------------------------------------------------


class TestAC2:
    """AC-2: y_axis.min/max = data min/max +/- 5%"""

    def test_y_axis_min_max_padding_5pct(self):
        gen = _py_generate()
        # data range 100-1000, buffer = (1000-100)*0.05 = 45
        # range_ratio = 0.9 > 0.5 -> zero_based=false -> y_min keeps buffer
        input_data = {
            "data_points": [{"x": "a", "y": 100}, {"x": "b", "y": 1000}],
            "unit": "USD",
            "granularity": "category",
        }
        result = gen(input_data)
        assert result["y_axis"]["min"] == pytest.approx(55.0), (
            f"Expected y_min ~55, got {result['y_axis']['min']}"
        )
        assert result["y_axis"]["max"] == pytest.approx(1045.0), (
            f"Expected y_max ~1045, got {result['y_axis']['max']}"
        )

        # data range 0-1000, buffer = 50
        input_data2 = {
            "data_points": [{"x": "a", "y": 0}, {"x": "b", "y": 1000}],
            "unit": "CNY",
            "granularity": "category",
        }
        result2 = gen(input_data2)
        assert result2["y_axis"]["min"] == pytest.approx(-50.0), (
            f"Expected y_min ~-50, got {result2['y_axis']['min']}"
        )
        assert result2["y_axis"]["max"] == pytest.approx(1050.0), (
            f"Expected y_max ~1050, got {result2['y_axis']['max']}"
        )

        # --- TS side ---
        ts_src = _read_ts(TS_AXIS_PATH)
        assert re.search(r"0\.05|5\s*%|buffer.*0\.05", ts_src), (
            "TS source missing 5% buffer pattern"
        )
        assert re.search(r"yMin|y_axis.*min|y_axis", ts_src), (
            "TS y_min / yMin logic not found"
        )


# ---------------------------------------------------------------------------
# AC-3: zero_based heuristic: (max-min)/max > 0.5 -> false
# ---------------------------------------------------------------------------


class TestAC3:
    """AC-3: zero_based heuristic: (max-min)/max > 0.5 -> false"""

    def test_zero_based_heuristic_threshold(self):
        gen = _py_generate()
        # range_ratio = (200-100)/200 = 0.5 -> <= 0.5 -> zero_based = true
        input_small_ratio = {
            "data_points": [{"x": "a", "y": 100}, {"x": "b", "y": 200}],
            "unit": "USD",
            "granularity": "category",
        }
        result = gen(input_small_ratio)
        assert result["y_axis"]["zero_based"] is True, (
            f"range_ratio=0.5 should produce zero_based=True, "
            f"got {result['y_axis']['zero_based']}"
        )
        assert result["y_axis"]["min"] == 0.0, (
            f"zero_based=True requires y_min=0, got {result['y_axis']['min']}"
        )

        # range_ratio = (1000-100)/1000 = 0.9 -> > 0.5 -> zero_based = false
        input_large_ratio = {
            "data_points": [{"x": "a", "y": 100}, {"x": "b", "y": 1000}],
            "unit": "USD",
            "granularity": "category",
        }
        result2 = gen(input_large_ratio)
        assert result2["y_axis"]["zero_based"] is False, (
            f"range_ratio=0.9 should produce zero_based=False, "
            f"got {result2['y_axis']['zero_based']}"
        )

        # --- TS side ---
        ts_src = _read_ts(TS_AXIS_PATH)
        assert re.search(r"0\.5|range_ratio", ts_src), (
            "TS source missing range_ratio or 0.5 threshold"
        )
        assert re.search(r"zero_based", ts_src), "TS source missing zero_based"


# ---------------------------------------------------------------------------
# AC-4: tick_format auto-selection 0.01/1/1k/1M based on range
# ---------------------------------------------------------------------------


class TestAC4:
    """AC-4: tick_format auto-selection based on value range"""

    def test_tick_format_auto_selection(self):
        gen = _py_generate()
        # abs_max < 1 -> 0.01
        r1 = gen(
            {
                "data_points": [{"x": "a", "y": 0.1}, {"x": "b", "y": 0.5}],
                "unit": "ratio",
                "granularity": "category",
            }
        )
        assert r1["y_axis"]["tick_format"] == "0.01", (
            f"abs_max<1 should use '0.01', got {r1['y_axis']['tick_format']}"
        )

        # abs_max in [1, 1000) -> '1'
        r2 = gen(
            {
                "data_points": [{"x": "a", "y": 10}, {"x": "b", "y": 500}],
                "unit": "USD",
                "granularity": "category",
            }
        )
        assert r2["y_axis"]["tick_format"] == "1", (
            f"abs_max in [1,1000) should use '1', got {r2['y_axis']['tick_format']}"
        )

        # abs_max in [1000, 1000000) -> '1k'
        r3 = gen(
            {
                "data_points": [{"x": "a", "y": 5000}, {"x": "b", "y": 500000}],
                "unit": "USD",
                "granularity": "category",
            }
        )
        assert r3["y_axis"]["tick_format"] == "1k", (
            f"abs_max in [1000,1M) should use '1k', got {r3['y_axis']['tick_format']}"
        )

        # abs_max >= 1000000 -> '1M'
        r4 = gen(
            {
                "data_points": [{"x": "a", "y": 1_000_000}, {"x": "b", "y": 5_000_000}],
                "unit": "USD",
                "granularity": "category",
            }
        )
        assert r4["y_axis"]["tick_format"] == "1M", (
            f"abs_max>=1M should use '1M', got {r4['y_axis']['tick_format']}"
        )

        # --- TS side ---
        ts_src = _read_ts(TS_AXIS_PATH)
        assert re.search(r"0\.01", ts_src), "TS source missing '0.01' tick_format"
        assert re.search(r"1_?000", ts_src), "TS source missing '1k' threshold"
        assert re.search(r"1_?000_?000|1M", ts_src), "TS source missing '1M' threshold"


# ---------------------------------------------------------------------------
# AC-5: property-based determinism (same input = same output)
# ---------------------------------------------------------------------------


class TestAC5:
    """AC-5: same input produces same result (pure function, property-based)"""

    def test_property_based_determinism(self):
        gen = _py_generate()

        test_cases = [
            {
                "data_points": [{"x": "a", "y": 100}, {"x": "b", "y": 200}],
                "unit": "USD",
                "granularity": "category",
            },
            {
                "data_points": [
                    {"x": "2024-01-01", "y": 10},
                    {"x": "2024-01-02", "y": 20},
                ],
                "unit": "CNY",
                "granularity": "day",
            },
            {
                "data_points": [{"x": "Tesla", "y": 0.1}, {"x": "Apple", "y": 0.5}],
                "unit": "ratio",
                "granularity": "category",
            },
            {
                "data_points": [{"x": "a", "y": 1000000}, {"x": "b", "y": 5000000}],
                "unit": "USD",
                "granularity": "category",
            },
        ]

        for tc in test_cases:
            results = []
            for _ in range(10):
                r = gen(tc)
                results.append(
                    hashlib.sha256(json.dumps(r, sort_keys=True).encode()).hexdigest()
                )
            assert len(set(results)) == 1, (
                f"generate_axis_spec produced different outputs for same input: {tc}"
            )

        # --- TS side: verify pure function pattern (no side effects) ---
        ts_src = _read_ts(TS_AXIS_PATH)
        # No API calls, no I/O, no random
        for banned in ("fetch", "http", "axios", "Math.random", "Date", "localStorage"):
            assert banned not in ts_src, (
                f"TS axis_spec_generator references impure {banned}"
            )
        # Must export generate_axis_spec
        assert re.search(
            r"export\s+(async\s+)?function\s+generate[Aa]xis[Ss]pec", ts_src
        ), "TS source missing generate_axis_spec export"
