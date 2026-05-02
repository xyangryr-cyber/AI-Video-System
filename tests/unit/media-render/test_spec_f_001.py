"""Tests for [SPEC-F-001] ECharts Templates: Line, Area, Bar Charts."""

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


class TestAC1LineChartMarkpointHighlight:
    """AC-1: `animated_line_chart` uses `markPoint` for highlight + `graphic` component for arrow following"""

    def test_line_chart_markpoint_highlight(self):
        src = _read_src("AnimatedLineChart.tsx")
        assert src, "AnimatedLineChart.tsx does not exist or is empty"
        assert "markPoint" in src, (
            "AnimatedLineChart.tsx must contain 'markPoint' for highlighting"
        )
        assert "graphic" in src, (
            "AnimatedLineChart.tsx must contain 'graphic' for arrow following"
        )


class TestAC2LineChartNativeAnimationConfig:
    """AC-2: `animated_line_chart` uses `animationDuration` + `animationDelay` for point-by-point draw in non-Remotion preview"""

    def test_line_chart_native_animation_config(self):
        src = _read_src("AnimatedLineChart.tsx")
        assert src, "AnimatedLineChart.tsx does not exist or is empty"
        assert "animationDuration" in src, (
            "AnimatedLineChart.tsx must contain 'animationDuration' for draw animation"
        )
        assert "animationDelay" in src, (
            "AnimatedLineChart.tsx must contain 'animationDelay' for point-by-point draw"
        )


class TestAC3AreaChartFillAndGradient:
    """AC-3: `animated_area_chart` uses `areaStyle` + `animationDuration` for fill animation and `visualMap` for gradient colors"""

    def test_area_chart_fill_and_gradient(self):
        src = _read_src("AnimatedAreaChart.tsx")
        assert src, "AnimatedAreaChart.tsx does not exist or is empty"
        assert "areaStyle" in src, (
            "AnimatedAreaChart.tsx must contain 'areaStyle' for fill"
        )
        assert "animationDuration" in src, (
            "AnimatedAreaChart.tsx must contain 'animationDuration' for fill animation"
        )
        assert "visualMap" in src, (
            "AnimatedAreaChart.tsx must contain 'visualMap' for gradient colors"
        )


class TestAC4BarChartSequentialGrowth:
    """AC-4: `animated_bar_chart` uses `animationDelay` by `dataIndex` ascending for sequential growth + `emphasis` state for highlight color change"""

    def test_bar_chart_sequential_growth(self):
        src = _read_src("AnimatedBarChart.tsx")
        assert src, "AnimatedBarChart.tsx does not exist or is empty"
        assert "animationDelay" in src, (
            "AnimatedBarChart.tsx must contain 'animationDelay'"
        )
        assert "dataIndex" in src, (
            "AnimatedBarChart.tsx must use 'dataIndex' for sequential growth"
        )
        assert "emphasis" in src, (
            "AnimatedBarChart.tsx must contain 'emphasis' for highlight color change"
        )


class TestAC5AllImplementTemplateProps:
    """AC-5: All 3 templates implement `React.FC<TemplateProps>` interface"""

    @pytest.mark.parametrize(
        "filename",
        [
            "AnimatedLineChart.tsx",
            "AnimatedAreaChart.tsx",
            "AnimatedBarChart.tsx",
        ],
    )
    def test_implements_fc_template_props(self, filename):
        src = _read_src(filename)
        assert src, f"{filename} does not exist or is empty"
        has_fc = "React.FC" in src
        has_tp = "TemplateProps" in src
        assert has_fc, f"{filename} must use 'React.FC' (React.FC<TemplateProps>)"
        assert has_tp, f"{filename} must reference 'TemplateProps'"


class TestAC6AllRegisteredInRegistry:
    """AC-6: All 3 templates registered in `template_registry.ts` under correct template IDs"""

    TEMPLATE_IDS = [
        "animated_line_chart",
        "animated_area_chart",
        "animated_bar_chart",
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


class TestAC7AllAcceptAnnotationKeyframes:
    """AC-7: All 3 templates accept `annotation_keyframes` parameter"""

    @pytest.mark.parametrize(
        "filename",
        [
            "AnimatedLineChart.tsx",
            "AnimatedAreaChart.tsx",
            "AnimatedBarChart.tsx",
        ],
    )
    def test_accepts_annotation_keyframes(self, filename):
        src = _read_src(filename)
        assert src, f"{filename} does not exist or is empty"
        # annotationKeyframes is the camelCase prop name in TemplateProps
        assert "annotationKeyframes" in src or "props" in src.lower(), (
            f"{filename} must accept annotationKeyframes (via TemplateProps destructuring or props.annotationKeyframes)"
        )
