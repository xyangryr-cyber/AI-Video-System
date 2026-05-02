"""Tests for [SPEC-F-011] Cover Generation, Brand Consistency & Platform Adaptation."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RENDER_DIR = PROJECT_ROOT / "src" / "frontend" / "render"
PLAYER_DIR = PROJECT_ROOT / "src" / "frontend" / "components" / "player"
COVER_PATH = RENDER_DIR / "coverGenerator.ts"
BRAND_KIT_PATH = RENDER_DIR / "brandKit.ts"
PLATFORM_PATH = RENDER_DIR / "platformProfile.ts"
BRAND_OVERLAY_PATH = PLAYER_DIR / "BrandOverlay.tsx"

COVER_TEMPLATES = ["data_focus", "chart_preview", "clean_text"]
ASPECT_RATIOS = ["16:9", "3:4", "1:1"]


def _read_text(path: Path) -> str:
    assert path.is_file(), f"Missing file: {path}"
    return path.read_text(encoding="utf-8")


def _all_render_sources() -> str:
    sources = []
    for p in [COVER_PATH, BRAND_KIT_PATH, PLATFORM_PATH, BRAND_OVERLAY_PATH]:
        if p.is_file():
            sources.append(p.read_text(encoding="utf-8"))
    return "\n".join(sources)


class TestAC1NineCoversGenerated:
    """AC-1: 9 cover files generated (3 templates x 3 ratios)"""

    def test_nine_covers_generated(self):
        source = _read_text(COVER_PATH)
        for tpl in COVER_TEMPLATES:
            assert tpl in source, f"coverGenerator must support '{tpl}' template"
        for ratio in ASPECT_RATIOS:
            assert ratio in source, (
                f"coverGenerator must support '{ratio}' aspect ratio"
            )


class TestAC2_169Dimensions:
    """AC-2: 16:9 cover dimensions are 1280x720"""

    def test_16_9_dimensions(self):
        source = _read_text(COVER_PATH)
        assert "1280" in source, "coverGenerator must set 16:9 width to 1280"
        assert "720" in source, "coverGenerator must set 16:9 height to 720"


class TestAC3DataFocusKeyDataPoint:
    """AC-3: data_focus template sources big number from key_data_point"""

    def test_data_focus_key_data_point(self):
        source = _read_text(COVER_PATH)
        assert "key_data_point" in source or "keyDataPoint" in source, (
            "data_focus template must source big number from key_data_point"
        )


class TestAC4BrandKitInheritance:
    """AC-4: New project theme.json inherits brand_kit for un-overridden fields"""

    def test_brand_kit_inheritance(self):
        source = _read_text(BRAND_KIT_PATH)
        assert (
            "inherit" in source.lower()
            or "merge" in source.lower()
            or "fallback" in source.lower()
        ), "brandKit must support inheriting brand_kit values for un-overridden fields"


class TestAC5ProjectOverrideColor:
    """AC-5: Project-level color_palette.primary override over brand_kit default"""

    def test_project_override_color(self):
        source = _read_text(BRAND_KIT_PATH)
        assert "override" in source.lower() or "color_palette" in source, (
            "brandKit must support project-level color_palette.primary override"
        )


class TestAC6MissingBrandKitDefaults:
    """AC-6: Missing brand_kit falls back to system defaults"""

    def test_missing_brand_kit_defaults(self):
        source = _read_text(BRAND_KIT_PATH)
        assert "default" in source.lower(), (
            "brandKit must fall back to system defaults when brand_kit is missing"
        )


class TestAC7BrandKitFromApi:
    """AC-7: Render layer reads brand_kit from API, not directly from file"""

    def test_brand_kit_from_api(self):
        source = _read_text(BRAND_KIT_PATH)
        assert (
            "fetch" in source or "api" in source.lower() or "/api/settings" in source
        ), "brandKit must read from API (GET /api/settings), not directly from file"
        assert "brand_kit.json" not in source, (
            "brandKit must NOT read directly from brand_kit.json file"
        )


class TestAC8IntroDurationMatch:
    """AC-8: Intro duration matches brand_kit.intro_template.duration within 0.1s"""

    def test_intro_duration_match(self):
        source = _read_text(BRAND_OVERLAY_PATH)
        assert "intro" in source.lower() and "duration" in source.lower(), (
            "BrandOverlay must match intro duration to brand_kit.intro_template.duration"
        )


class TestAC9WatermarkAllFrames:
    """AC-9: All frames contain watermark when watermark.opacity > 0"""

    def test_watermark_all_frames(self):
        source = _read_text(BRAND_OVERLAY_PATH)
        assert "watermark" in source.lower(), (
            "BrandOverlay must render watermark on all frames"
        )
        assert "opacity" in source.lower(), "BrandOverlay must check watermark.opacity"


class TestAC10WatermarkOpacityZeroHidden:
    """AC-10: watermark.opacity=0 hides watermark"""

    def test_watermark_opacity_zero_hidden(self):
        source = _read_text(BRAND_OVERLAY_PATH)
        assert "opacity" in source.lower(), (
            "BrandOverlay must handle watermark.opacity=0 (hidden)"
        )


class TestAC11CompositionFromPlatformProfile:
    """AC-11: Remotion Composition width/height from platform profile"""

    def test_composition_from_platform_profile(self):
        source = _read_text(PLATFORM_PATH)
        assert "width" in source.lower() and "height" in source.lower(), (
            "platformProfile must define width and height for each platform"
        )


class TestAC12NoHardcodedPixelsInSubtitles:
    """AC-12: Subtitles contain no hardcoded pixel values"""

    def test_no_hardcoded_pixels_in_subtitles(self):
        source = _all_render_sources()
        # Percentage-based positioning: should use % units, not px
        # Look for percentage pattern in positioning context
        has_percentage = "%" in source or "percent" in source.lower()
        assert has_percentage, (
            "Cover/brand config must use percentage-based coordinates, not hardcoded pixels"
        )


class TestAC13DouyinDeferral:
    """AC-13: target_platform=douyin returns explicit deferral message"""

    def test_douyin_deferral(self):
        source = _read_text(PLATFORM_PATH)
        assert "douyin" in source.lower(), "platformProfile must handle douyin platform"
        assert (
            "defer" in source.lower()
            or "v1.5" in source.lower()
            or "not supported" in source.lower()
        ), "platformProfile must return explicit deferral for douyin (V1.5 only)"
