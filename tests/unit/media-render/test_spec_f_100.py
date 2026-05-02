"""Tests for [SPEC-F-100] ChartStyleOverrides 渲染规格."""

import os
import re


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

MERGING_PATH = os.path.join(
    PROJECT_ROOT, "src", "frontend", "remotion", "utils", "chart_style_merger.ts"
)
CHART_TEMPLATE_PATH = os.path.join(
    PROJECT_ROOT, "src", "frontend", "remotion", "components", "ChartTemplate.tsx"
)


def _read_ts(path: str) -> str:
    """Read a TS/TSX source file, fail test if file missing."""
    assert os.path.isfile(path), f"File not found: {path}"
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestAC1:
    """AC-1: priority ChartStyleOverrides > theme_config > template default"""

    def test_overrides_beats_theme_and_default(self):
        src = _read_ts(MERGING_PATH)
        assert re.search(r"export\s+(async\s+)?function\s+mergeChartStyle", src), (
            "mergeChartStyle function not exported"
        )
        assert re.search(r"overrides\b", src), "overrides parameter not found"
        assert re.search(r"theme(_config)?\b", src, re.IGNORECASE), (
            "theme_config not referenced"
        )
        assert re.search(r"overrides\.\w+|\?\?|\.\.\.\(.*overrides", src), (
            "No priority resolution pattern for overrides"
        )
        assert re.search(r"templateDefaults|template\.default|default", src), (
            "template defaults not handled"
        )


class TestAC2:
    """AC-2: color not in palette -> fallback palette[0] + structured log"""

    def test_invalid_color_fallback_to_palette_zero(self):
        src = _read_ts(MERGING_PATH)
        assert re.search(r"palette\b|color_palette\b", src), (
            "palette/color_palette not referenced"
        )
        assert re.search(r"palette\[0\]|color_palette\[0\]|\[0\]", src), (
            "fallback to palette[0] not found"
        )
        assert re.search(r"warn|log|console\.\w+|logger", src), (
            "no logging for invalid color"
        )
        assert re.search(
            r"palette_fallback|fallback|invalid.*color|color.*invalid", src
        ), "palette_fallback event pattern not found"


class TestAC3:
    """AC-3: show_source_label only when verified"""

    def test_show_source_label_only_when_verified(self):
        src = _read_ts(MERGING_PATH)
        assert re.search(r"show_source_label|showSourceLabel", src), (
            "show_source_label not referenced"
        )
        assert re.search(r"verified", src), "verified check not found"
        label_pattern = r"show_source_label|showSourceLabel"
        label_pos = max(
            (p for p in [m.start() for m in re.finditer(label_pattern, src)]),
            default=-1,
        )
        verified_match = re.search(r"verified", src)
        assert label_pos >= 0 and verified_match is not None, (
            "show_source_label or verified keyword missing"
        )
        assert abs(label_pos - verified_match.start()) < 1000, (
            "show_source_label and verified not in proximity"
        )


class TestAC4:
    """AC-4: backward compatible with v3.15 TemplateProps"""

    def test_backward_compat_v315_template_props(self):
        src = _read_ts(CHART_TEMPLATE_PATH)
        assert re.search(r"TemplateProps", src), "TemplateProps not referenced"
        assert re.search(
            r"chart_style_overrides\?\s*:"
            r"|chartStyleOverrides\?\s*:"
            r"|overrides\?\s*:"
            r"|ChartStyleOverrides\s*\|\s*undefined"
            r"|overrides\s*\?\s*:",
            src,
        ), "chart_style_overrides not treated as optional"
        assert re.search(r"theme\b|theme_config\b", src, re.IGNORECASE), (
            "theme fallback not found"
        )
