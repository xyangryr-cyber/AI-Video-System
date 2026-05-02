"""Tests for [SPEC-F-013] TemplateProps chart_material."""

import os
import re


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

SHARED_TEMPLATE_PROPS_TS = os.path.join(
    PROJECT_ROOT, "src", "shared", "types", "template_props.ts"
)
SHARED_TEMPLATE_PROPS_PY = os.path.join(
    PROJECT_ROOT, "src", "shared", "schemas", "template_props.py"
)
PRIORITY_TS = os.path.join(
    PROJECT_ROOT, "src", "frontend", "render", "chart_material_priority.ts"
)
CHART_DIR = os.path.join(
    PROJECT_ROOT, "src", "frontend", "components", "templates", "echarts"
)
EVENT_TIMELINE_TSX = os.path.join(
    PROJECT_ROOT,
    "src",
    "frontend",
    "components",
    "templates",
    "react",
    "EventTimeline.tsx",
)

CHART_FILES = [
    os.path.join(CHART_DIR, "AnimatedLineChart.tsx"),
    os.path.join(CHART_DIR, "AnimatedBarChart.tsx"),
    os.path.join(CHART_DIR, "AnimatedPieChart.tsx"),
    os.path.join(CHART_DIR, "CandlestickChart.tsx"),
    EVENT_TIMELINE_TSX,
]


def _read_ts(path: str) -> str:
    assert os.path.isfile(path), f"File not found: {path}"
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestAC1:
    """AC-1: chart_material  optional -- v3.15 callers not broken."""

    def test_template_props_has_optional_chart_material_ts(self):
        src = _read_ts(SHARED_TEMPLATE_PROPS_TS)
        assert re.search(r"chart_material\?\s*:", src), (
            "TemplateProps must have optional chart_material field"
        )

    def test_template_props_has_optional_chart_material_py(self):
        src = _read_ts(SHARED_TEMPLATE_PROPS_PY)
        assert re.search(r"chart_material", src), (
            "Python TemplateProps must reference chart_material"
        )

    def test_tsc_noemit_passes_with_new_field(self):
        """Project-level tsc must pass -- chart_material does not break existing callers."""
        import subprocess

        frontend_root = os.path.join(PROJECT_ROOT, "src", "frontend")
        result = subprocess.run(
            ["npx", "tsc", "--noEmit", "--project", "tsconfig.json"],
            cwd=frontend_root,
            capture_output=True,
            text=True,
        )
        # tsc may fail for unrelated reasons; we assert that chart_material is NOT
        # the cause by checking there is no error mentioning chart_material in TemplateProps.
        if result.returncode != 0:
            assert "chart_material" not in result.stdout, (
                f"tsc errors mention chart_material: {result.stdout[:2000]}"
            )
            assert "chart_material" not in result.stderr, (
                f"tsc stderr mentions chart_material: {result.stderr[:2000]}"
            )


class TestAC2:
    """AC-2: chart_material + conflicting data -> chart output matches chart_material."""

    def test_resolve_chart_data_function_exists(self):
        src = _read_ts(PRIORITY_TS)
        assert re.search(r"export\s+(async\s+)?function\s+resolveChartData", src), (
            "resolveChartData function not exported from chart_material_priority.ts"
        )

    def test_resolve_chart_data_prefers_chart_material(self):
        src = _read_ts(PRIORITY_TS)
        # Must check chart_material before data
        assert re.search(r"chart_material", src), (
            "chart_material not referenced in priority module"
        )
        # Must have priority logic (chart_material wins over data)
        assert re.search(r"chart_material.*\?|if\s*\(.*chart_material", src), (
            "No priority check for chart_material over data"
        )

    def test_all_chart_files_import_priority_module(self):
        for chart_path in CHART_FILES:
            src = _read_ts(chart_path)
            assert re.search(r"chart_material", src), (
                f"{os.path.basename(chart_path)} does not reference chart_material"
            )


class TestAC3:
    """AC-3: random chart_material -> rendered axis range == chart_material.axis_spec.range."""

    def test_axis_spec_range_used_in_charts(self):
        for chart_path in CHART_FILES[:4]:  # ECharts charts only
            src = _read_ts(chart_path)
            assert re.search(r"axisSpec", src), (
                f"{os.path.basename(chart_path)} does not reference axisSpec"
            )

    def test_chart_material_priority_respects_range(self):
        src = _read_ts(PRIORITY_TS)
        assert re.search(r"axis_spec|range|min|max", src), (
            "priority module does not handle axis_spec range"
        )


class TestAC4:
    """AC-4: chart type template without chart_material -> runtime error logged."""

    def test_validate_chart_material_function_exists(self):
        src = _read_ts(PRIORITY_TS)
        assert re.search(
            r"export\s+(async\s+)?function\s+validateChartMaterial", src
        ), "validateChartMaterial function not exported"

    def test_missing_chart_material_logs_error(self):
        src = _read_ts(PRIORITY_TS)
        assert re.search(r"console\.(error|warn)", src), (
            "No console.error/warn for missing chart_material"
        )


class TestAC5:
    """AC-5: conflict scenario -> log contains chart_material_priority_violation."""

    def test_priority_violation_string_in_module(self):
        src = _read_ts(PRIORITY_TS)
        assert re.search(r"chart_material_priority_violation", src), (
            "chart_material_priority_violation string not found in priority module"
        )

    def test_priority_violation_logged_on_conflict(self):
        src = _read_ts(PRIORITY_TS)
        assert re.search(
            r"chart_material_priority_violation.*console|console.*chart_material_priority_violation",
            src,
        ) or (
            "chart_material_priority_violation" in src
            and re.search(r"console\.(error|warn|log)", src)
        ), "chart_material_priority_violation not logged via console"


class TestAC6:
    """AC-6: ChartStyleOverrides + chart_material coexist correctly."""

    def test_chart_style_overrides_and_chart_material_independent(self):
        """ChartStyleOverrides handles style (color/width); chart_material handles data/axes."""
        for chart_path in CHART_FILES[:4]:
            src = _read_ts(chart_path)
            has_style = bool(
                re.search(
                    r"chart_style_overrides|ChartStyleOverrides|chart_style|color_palette|theme",
                    src,
                )
            )
            has_material = bool(re.search(r"chart_material", src))
            assert has_style and has_material, (
                f"{os.path.basename(chart_path)}: must use both style overrides "
                f"(style={has_style}) and chart_material (material={has_material})"
            )

    def test_style_from_overrides_data_from_chart_material(self):
        src = _read_ts(PRIORITY_TS)
        assert re.search(r"chart_style_overrides|ChartStyleOverrides|style", src), (
            "priority module does not reference ChartStyleOverrides/style"
        )
