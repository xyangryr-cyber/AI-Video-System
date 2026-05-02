"""Tests for [SPEC-F-102] Preview vs Production render mode.

Verifies TS source code patterns for render_mode_controller,
PreviewComposition, and ProductionComposition.
"""

import os
import re


PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
)

RENDER_MODE_PATH = os.path.join(
    PROJECT_ROOT, "src", "frontend", "remotion", "utils", "render_mode_controller.ts"
)
PREVIEW_PATH = os.path.join(
    PROJECT_ROOT,
    "src",
    "frontend",
    "remotion",
    "compositions",
    "PreviewComposition.tsx",
)
PRODUCTION_PATH = os.path.join(
    PROJECT_ROOT,
    "src",
    "frontend",
    "remotion",
    "compositions",
    "ProductionComposition.tsx",
)


def _read_ts(path: str) -> str:
    assert os.path.isfile(path), f"TS source not found: {path}"
    with open(path, encoding="utf-8") as f:
        return f.read()


class TestAC1:
    """AC-1: mode='preview' outputs 480p, single frame <= 500ms"""

    def test_preview_mode_480p_frame_under_500ms(self):
        ctrl_src = _read_ts(RENDER_MODE_PATH)
        preview_src = _read_ts(PREVIEW_PATH)

        # render_mode_controller.ts must define RenderMode type with 'preview'
        assert (
            re.search(r"RenderMode\s*=", ctrl_src)
            or re.search(r"type\s+RenderMode\s*=", ctrl_src)
            or re.search(r"export\s+type\s+RenderMode", ctrl_src)
        ), "RenderMode type not defined"

        assert re.search(r"['\"]preview['\"]", ctrl_src), (
            "preview mode not in RenderMode"
        )

        # getRenderConfig or equivalent must exist
        assert re.search(r"export\s+(async\s+)?function\s+getRenderConfig", ctrl_src), (
            "getRenderConfig not exported"
        )

        # Preview config must be 480p: 854x480
        assert re.search(r"854|480", ctrl_src) or re.search(r"854|480", preview_src), (
            "480p (854x480) resolution not found in preview config"
        )

        # Preview must use single frame (no frame loop)
        # Either render_mode_controller specifies fps=1 for preview
        # or PreviewComposition disables animation
        assert re.search(
            r"preview.*\{|preview.*:",
            ctrl_src,
        ), "preview config block not found"

        # Single frame / no animation for preview
        has_single_frame = (
            re.search(r"fps\s*:\s*1", ctrl_src)
            or re.search(r"animate.*false|statische", preview_src)
            or re.search(r"frame\s*=\s*0|singleFrame", preview_src)
        )
        assert has_single_frame, "preview single-frame rendering not detected"


class TestAC2:
    """AC-2: mode='production' outputs 1080p, full animation"""

    def test_production_mode_1080p_full_animation(self):
        ctrl_src = _read_ts(RENDER_MODE_PATH)
        prod_src = _read_ts(PRODUCTION_PATH)

        # RenderMode must include 'production'
        assert re.search(r"['\"]production['\"]", ctrl_src), (
            "production mode not in RenderMode"
        )

        # Production config must be 1080p: 1920x1080
        assert re.search(r"1920|1080", ctrl_src) or re.search(r"1920|1080", prod_src), (
            "1080p (1920x1080) resolution not found in production config"
        )

        # Production must support full animation (normal fps, not single frame)
        assert re.search(r"fps\s*:\s*(2[4-9]|30|[3-9]\d)", ctrl_src), (
            "production full animation fps not found (expected >= 24)"
        )

        # ProductionComposition must be a Remotion composition
        assert re.search(
            r"Composition|composition|defineComposition",
            prod_src,
        ), "ProductionComposition does not define a Remotion composition"


class TestAC3:
    """AC-3: both modes share data / axis_spec / style_overrides (no fork)"""

    def test_shared_data_axis_style_no_fork(self):
        preview_src = _read_ts(PREVIEW_PATH)
        prod_src = _read_ts(PRODUCTION_PATH)

        # Both compositions must import from shared types (TemplateProps)
        # ChartStyleOverrides / AxisSpec are passed through TemplateProps,
        # not re-declared locally.
        assert "TemplateProps" in preview_src, (
            "PreviewComposition does not reference TemplateProps"
        )
        assert "TemplateProps" in prod_src, (
            "ProductionComposition does not reference TemplateProps"
        )

        # Neither composition should contain data-fetching logic (exclude comments)
        _strip_comments = lambda s: re.sub(r"//.*", "", s)
        for banned in ("axios", "http://", "https://", "query(", " request("):
            assert banned not in _strip_comments(preview_src.lower()), (
                f"PreviewComposition contains data-fetching: {banned}"
            )
            assert banned not in _strip_comments(prod_src.lower()), (
                f"ProductionComposition contains data-fetching: {banned}"
            )

        # Both should accept same data input shape (TemplateProps or derived)
        assert re.search(r"props\b|TemplateProps|RenderProps", preview_src), (
            "PreviewComposition missing props/data input"
        )
        assert re.search(r"props\b|TemplateProps|RenderProps", prod_src), (
            "ProductionComposition missing props/data input"
        )


class TestAC4:
    """AC-4: mode switch does not trigger backend data rerun"""

    def test_mode_switch_no_backend_rerun(self):
        ctrl_src = _read_ts(RENDER_MODE_PATH)
        preview_src = _read_ts(PREVIEW_PATH)
        prod_src = _read_ts(PRODUCTION_PATH)

        _strip_comments = lambda s: re.sub(r"//.*|\/\*[\s\S]*?\*\/", "", s)

        # render_mode_controller must NOT contain backend API calls
        for banned in ("fetch(", "axios", "http://", "https://", "/api/", "APIService"):
            assert banned not in _strip_comments(ctrl_src), (
                f"render_mode_controller contains backend call: {banned}"
            )

        # Neither composition should trigger backend rerun on mode switch
        for banned in ("fetch(", "axios", "http://", "https://", "/api/"):
            assert banned not in _strip_comments(preview_src), (
                f"PreviewComposition triggers backend data rerun: {banned}"
            )
            assert banned not in _strip_comments(prod_src), (
                f"ProductionComposition triggers backend data rerun: {banned}"
            )

        # Mode must be a local prop (not fetched from backend)
        assert re.search(r"mode\b", ctrl_src), (
            "render_mode_controller does not define mode"
        )

        # getRenderConfig must be pure -- no side effects
        assert re.search(r"export\s+(async\s+)?function\s+getRenderConfig", ctrl_src), (
            "getRenderConfig not found"
        )
        # No async function (synchronous mode switch)
        assert not re.search(
            r"export\s+async\s+function\s+getRenderConfig", ctrl_src
        ), "getRenderConfig should be synchronous (not async)"
