"""Tests for [SPEC-F-002] ECharts Templates: Pie, Treemap, Number Callout."""

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


class TestAC1PieChartRotationalRevealAndExplode:
    """AC-1: `animated_pie_chart` uses `startAngle` + `animationDuration` for rotational reveal + `selectedMode` for sector explode"""

    def test_pie_chart_rotational_reveal_and_explode(self):
        src = _read_src("AnimatedPieChart.tsx")
        assert src, "AnimatedPieChart.tsx does not exist or is empty"
        assert "startAngle" in src, (
            "AnimatedPieChart.tsx must contain 'startAngle' for rotational reveal"
        )
        assert "animationDuration" in src, (
            "AnimatedPieChart.tsx must contain 'animationDuration'"
        )
        assert "selectedMode" in src, (
            "AnimatedPieChart.tsx must contain 'selectedMode' for sector explode"
        )


class TestAC2TreemapDrillDownAnimation:
    """AC-2: `treemap_chart` uses treemap series native `drillDown` + `animationDurationUpdate` for hierarchical expand"""

    def test_treemap_drill_down_animation(self):
        src = _read_src("TreemapChart.tsx")
        assert src, "TreemapChart.tsx does not exist or is empty"
        assert "drillDown" in src or "drill_down" in src, (
            "TreemapChart.tsx must contain 'drillDown' for hierarchical drill-down"
        )
        assert "animationDurationUpdate" in src, (
            "TreemapChart.tsx must contain 'animationDurationUpdate' for expand animation"
        )


class TestAC3NumberCalloutCountupAndPulse:
    """AC-3: `number_callout` uses `graphic` component for count-up animation + CSS `@keyframes` for pulse-scale effect"""

    def test_number_callout_countup_and_pulse(self):
        src = _read_src("NumberCallout.tsx")
        assert src, "NumberCallout.tsx does not exist or is empty"
        assert "graphic" in src, (
            "NumberCallout.tsx must contain 'graphic' for count-up animation"
        )
        assert "@keyframes" in src, (
            "NumberCallout.tsx must contain CSS '@keyframes' for pulse-scale effect"
        )


class TestAC4AllImplementTemplateProps:
    """AC-4: All 3 templates implement `React.FC<TemplateProps>` interface"""

    @pytest.mark.parametrize(
        "filename",
        [
            "AnimatedPieChart.tsx",
            "TreemapChart.tsx",
            "NumberCallout.tsx",
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
    """AC-5: All 3 templates registered in `template_registry.ts` under correct template IDs"""

    TEMPLATE_IDS = [
        "animated_pie_chart",
        "treemap_chart",
        "number_callout",
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


class TestAC6NumberCalloutParams:
    """AC-6: `number_callout` accepts `number, unit, count_up_duration, emphasis_color, comparison{}` params"""

    def test_number_callout_params(self):
        src = _read_src("NumberCallout.tsx")
        assert src, "NumberCallout.tsx does not exist or is empty"
        required_params = ["number", "count_up_duration", "emphasis_color"]
        for param in required_params:
            assert param in src, f"NumberCallout.tsx must reference '{param}' parameter"
        assert "unit" in src, "NumberCallout.tsx must reference 'unit' parameter"
        assert "comparison" in src, (
            "NumberCallout.tsx must reference 'comparison' object"
        )
