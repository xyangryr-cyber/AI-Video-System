"""Tests for [SPEC-F-003] ECharts Templates: Candlestick, Comparison Chart."""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
FRONTEND = REPO / "src" / "frontend"
TEMPLATES = FRONTEND / "components" / "templates" / "echarts"
REGISTRY_FILE = FRONTEND / "components" / "templates" / "template_registry.ts"


def _read_src(filename: str) -> str:
    """Read a TSX source file from the echarts templates directory."""
    p = TEMPLATES / filename
    if not p.exists():
        return ""
    return p.read_text()


def _read_registry() -> str:
    """Read the template_registry.ts content."""
    if not REGISTRY_FILE.exists():
        return ""
    return REGISTRY_FILE.read_text()


class TestAC1CandlestickThreeSeries:
    """AC-1: `candlestick_chart` contains `candlestick` + `line` (MA lines) + `bar` (volume) three series types"""

    def test_candlestick_three_series(self):
        src = _read_src("CandlestickChart.tsx")
        assert src, "CandlestickChart.tsx does not exist or is empty"
        assert "candlestick" in src, (
            "CandlestickChart.tsx must contain 'candlestick' series type"
        )
        assert "'line'" in src or '"line"' in src, (
            "CandlestickChart.tsx must contain 'line' series type for MA lines"
        )
        assert "'bar'" in src or '"bar"' in src, (
            "CandlestickChart.tsx must contain 'bar' series type for volume"
        )


class TestAC2CandlestickDatazoomAndDelay:
    """AC-2: `candlestick_chart` uses `dataZoom` for zoom control + `animationDelay` for sequential candle draw"""

    def test_candlestick_datazoom_and_delay(self):
        src = _read_src("CandlestickChart.tsx")
        assert src, "CandlestickChart.tsx does not exist or is empty"
        assert "dataZoom" in src, (
            "CandlestickChart.tsx must contain 'dataZoom' for zoom control"
        )
        assert "animationDelay" in src, (
            "CandlestickChart.tsx must contain 'animationDelay' for sequential draw"
        )


class TestAC3ComparisonSharedAxisAndDivergence:
    """AC-3: `comparison_chart` uses multiple `line`/`bar` series sharing `xAxis` + `markArea` + `markLine` for divergence highlight"""

    def test_comparison_shared_axis_and_divergence(self):
        src = _read_src("ComparisonChart.tsx")
        assert src, "ComparisonChart.tsx does not exist or is empty"
        assert "markArea" in src, (
            "ComparisonChart.tsx must contain 'markArea' for divergence highlight"
        )
        assert "markLine" in src, (
            "ComparisonChart.tsx must contain 'markLine' for divergence highlight"
        )
        # Check for shared xAxis: the xAxis config should be referenced once (shared)
        assert "xAxis" in src, (
            "ComparisonChart.tsx must contain 'xAxis' for shared axis"
        )


class TestAC4AllImplementTemplateProps:
    """AC-4: Both templates implement `React.FC<TemplateProps>` interface"""

    @pytest.mark.parametrize(
        "filename",
        [
            "CandlestickChart.tsx",
            "ComparisonChart.tsx",
        ],
    )
    def test_implements_fc_template_props(self, filename):
        src = _read_src(filename)
        assert src, f"{filename} does not exist or is empty"
        has_fc = "React.FC" in src
        has_tp = "TemplateProps" in src
        assert has_fc, f"{filename} must use 'React.FC' (React.FC<TemplateProps>)"
        assert has_tp, f"{filename} must reference 'TemplateProps'"


class TestAC5AllRegisteredInRegistry:
    """AC-5: Both templates registered in `template_registry.ts`"""

    TEMPLATE_IDS = [
        "candlestick_chart",
        "comparison_chart",
    ]

    def test_registry_file_exists(self):
        reg = _read_registry()
        assert reg, "template_registry.ts does not exist or is empty"

    @pytest.mark.parametrize("template_id", TEMPLATE_IDS)
    def test_template_registered(self, template_id):
        reg = _read_registry()
        assert template_id in reg, (
            f"template_registry.ts must contain entry for '{template_id}'"
        )
