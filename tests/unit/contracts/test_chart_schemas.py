"""Tests for [SPEC-A-103] ChartRequest / AxisSpec / ChartStyleOverrides.

Authority: docs/specs/SPEC-A-contracts.md §A-BDD-4 (SPEC-0A.11).

Covers AC-1 (7-value status enum) and AC-2 (AxisSpec zero_based on y_axis).
Re-exported by ``test_spec_a_103.py`` (A-100/A-101/A-102 pattern).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from pydantic import ValidationError

REPO_ROOT = Path(__file__).resolve().parents[3]
TS_PATH = REPO_ROOT / "src" / "shared" / "types" / "chart_request.ts"

EXPECTED_STATUSES = (
    "awaiting_clarification",
    "fetching",
    "awaiting_verification",
    "awaiting_confirmation",
    "rendering",
    "completed",
    "failed",
)


def _base_chart_request(**overrides):
    payload = {
        "request_id": "req_001",
        "user_intent": "画一张黄金价格折线图",
        "status": "awaiting_clarification",
    }
    payload.update(overrides)
    return payload


def _base_axis_spec(**overrides):
    payload = {
        "x_axis": {"type": "time", "label": "时间"},
        "y_axis": {
            "type": "value",
            "zero_based": False,
            "unit": "USD",
            "label": "价格",
        },
    }
    payload.update(overrides)
    return payload


class TestAC1ChartRequestStatusEnum:
    """AC-1: ChartRequest status enum has exactly 7 values."""

    def test_chart_request_status_enum_has_seven_values(self) -> None:
        from src.shared.schemas.chart_request import (
            ChartRequest,
            ChartRequestStatus,
        )
        from typing import get_args

        values = set(get_args(ChartRequestStatus))
        assert values == set(EXPECTED_STATUSES), (
            f"ChartRequestStatus must be exactly {EXPECTED_STATUSES} "
            f"(got {sorted(values)})"
        )
        assert len(values) == 7

        # Each of the 7 literals is accepted by the Pydantic model.
        for st in EXPECTED_STATUSES:
            model = ChartRequest(**_base_chart_request(status=st))
            assert model.status == st

        # Any other literal is rejected.
        with pytest.raises(ValidationError):
            ChartRequest(**_base_chart_request(status="cancelled"))
        with pytest.raises(ValidationError):
            ChartRequest(**_base_chart_request(status="draft"))

    def test_ts_mirror_lists_same_seven_statuses(self) -> None:
        assert TS_PATH.exists(), f"missing TS file: {TS_PATH}"
        src = TS_PATH.read_text(encoding="utf-8")
        m = re.search(
            r"export\s+type\s+ChartRequestStatus\s*=([^;]+);",
            src,
        )
        assert m, "ChartRequestStatus type alias not found in chart_request.ts"
        ts_values = set(re.findall(r'"([^"]+)"', m.group(1)))
        assert ts_values == set(EXPECTED_STATUSES), (
            f"TS ChartRequestStatus mismatch — "
            f"ts-only={ts_values - set(EXPECTED_STATUSES)}, "
            f"py-only={set(EXPECTED_STATUSES) - ts_values}"
        )


class TestAC2AxisSpecZeroBased:
    """AC-2: AxisSpec has x_axis/y_axis and y_axis supports zero_based bool."""

    def test_axis_spec_supports_zero_based_on_y_axis(self) -> None:
        from src.shared.schemas.axis_spec import AxisSpec

        # zero_based=True is accepted.
        model = AxisSpec(
            **_base_axis_spec(
                y_axis={
                    "type": "value",
                    "zero_based": True,
                    "unit": "USD",
                    "label": "价格",
                },
            )
        )
        assert model.y_axis.zero_based is True
        assert model.x_axis.type == "time"

        # zero_based=False is also accepted.
        model = AxisSpec(**_base_axis_spec())
        assert model.y_axis.zero_based is False

        # zero_based is REQUIRED on y_axis (not optional).
        with pytest.raises(ValidationError):
            AxisSpec(
                **_base_axis_spec(
                    y_axis={"type": "value", "unit": "USD", "label": "价格"}
                )
            )

        # Non-boolean zero_based is rejected.
        with pytest.raises(ValidationError):
            AxisSpec(
                **_base_axis_spec(
                    y_axis={
                        "type": "value",
                        "zero_based": "yes",
                        "unit": "USD",
                        "label": "价格",
                    }
                )
            )

        # x_axis does NOT carry zero_based (only y_axis does per SPEC).
        from src.shared.schemas.axis_spec import XAxisSpec

        assert "zero_based" not in XAxisSpec.model_fields

    def test_chart_request_embeds_axis_spec_with_zero_based(self) -> None:
        from src.shared.schemas.chart_request import ChartRequest

        req = ChartRequest(
            **_base_chart_request(
                status="rendering",
                axis_spec=_base_axis_spec(
                    y_axis={
                        "type": "value",
                        "zero_based": True,
                        "unit": "USD",
                        "label": "价格",
                    }
                ),
            )
        )
        assert req.axis_spec is not None
        assert req.axis_spec.y_axis.zero_based is True
