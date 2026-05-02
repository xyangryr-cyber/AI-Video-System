# [SPEC-F-101] AxisSpec auto-generator (Python, backend side).
# Pure deterministic function -- same input always produces same output.
# Mirrors the TypeScript version in src/frontend/remotion/utils/axis_spec_generator.ts.

from __future__ import annotations

from typing import Any

# Granularity values that map to x_axis type "time"
_TIME_GRANULARITIES = frozenset({"day", "week", "month", "quarter", "year"})


def _y_values(data_points: list[dict[str, Any]]) -> list[float]:
    """Extract y-values from data points."""
    return [float(p["y"]) for p in data_points]


def generate_axis_spec(input_data: dict[str, Any]) -> dict[str, Any]:
    """Generate AxisSpec from data points + metadata.

    Args:
        input_data: dict with keys:
            - data_points: list of {"x": str|number, "y": number}
            - unit: str
            - granularity: "day" | "week" | "month" | "quarter" | "year" | "category"

    Returns:
        dict with keys: x_axis, y_axis
    """
    data_points: list[dict[str, Any]] = input_data["data_points"]
    unit: str = input_data["unit"]
    granularity: str = input_data.get("granularity", "category")

    # --- x_axis type inference (AC-1) ---
    if granularity in _TIME_GRANULARITIES:
        x_type = "time"
    else:
        x_type = "category"

    # --- y_axis range with 5% buffer (AC-2) ---
    y_vals = _y_values(data_points)
    data_min = min(y_vals)
    data_max = max(y_vals)
    buffer = (data_max - data_min) * 0.05
    y_min = data_min - buffer
    y_max = data_max + buffer

    # --- zero_based heuristic (AC-3) ---
    # range_ratio = (data_max - data_min) / data_max, 1 if data_max is 0
    if data_max != 0:
        range_ratio = (data_max - data_min) / data_max
    else:
        range_ratio = 1.0
    zero_based = range_ratio <= 0.5
    if zero_based:
        y_min = 0.0

    # --- tick_format auto-select (AC-4) ---
    abs_max = max(abs(y_min), abs(y_max))
    if abs_max < 1:
        tick_format = "0.01"
    elif abs_max < 1_000:
        tick_format = "1"
    elif abs_max < 1_000_000:
        tick_format = "1k"
    else:
        tick_format = "1M"

    return {
        "x_axis": {
            "type": x_type,
        },
        "y_axis": {
            "min": y_min,
            "max": y_max,
            "zero_based": zero_based,
            "tick_format": tick_format,
            "unit_label": unit,
        },
    }
