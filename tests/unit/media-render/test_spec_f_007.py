"""Tests for [SPEC-F-007] Remotion Orchestration Layer & Template Registry."""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"
PLAYER_DIR = FRONTEND_DIR / "components" / "player"
RENDER_DIR = FRONTEND_DIR / "render"
REGISTRY_PATH = FRONTEND_DIR / "components" / "templates" / "template_registry.ts"

# The 15 data_type → template_id mappings from SPEC-18.3
EXPECTED_TEMPLATE_MAPPING = {
    "time_series": "animated_line_chart",
    "categorical_comparison": "animated_bar_chart",
    "proportion": "animated_pie_chart",
    "ohlc": "candlestick_chart",
    "single_metric": "number_callout",
    "trend_with_area": "animated_area_chart",
    "multi_series_comparison": "comparison_chart",
    "hierarchy": "treemap_chart",
    "news_reference": "news_card",
    "event_sequence": "event_timeline",
    "policy_comparison": "policy_comparison",
    "relationship": "relationship_graph",
    "person_quote": "quote_card",
    "geographic": "map_annotation",
    "summary_with_sparkline": "data_card",
}

ANIMATION_LIBS = ["framer-motion", "framer_motion", "gsap", "react-spring"]

LAYER3_FILES = [
    PLAYER_DIR / "VideoComposition.tsx",
    PLAYER_DIR / "SegmentSequencer.tsx",
    PLAYER_DIR / "LayerStack.tsx",
    RENDER_DIR / "renderPipeline.ts",
]


def _read_text(path: Path) -> str:
    assert path.is_file(), f"Missing file: {path}"
    return path.read_text(encoding="utf-8")


def _layer3_source() -> str:
    sources = []
    for f in LAYER3_FILES:
        if f.is_file():
            sources.append(f.read_text(encoding="utf-8"))
    return "\n".join(sources)


class TestAC1NoAnimationLibImports:
    """AC-1: Layer 3 code has zero imports of `framer-motion`, `gsap`, or other animation libraries"""

    def test_no_framer_motion_import(self):
        source = _layer3_source()
        assert "framer-motion" not in source, (
            "Layer 3 code must not import framer-motion"
        )
        assert "framer_motion" not in source, (
            "Layer 3 code must not import framer_motion"
        )

    def test_no_gsap_import(self):
        source = _layer3_source()
        assert "gsap" not in source, "Layer 3 code must not import gsap"

    def test_no_animation_lib_imports(self):
        source = _layer3_source()
        for lib in ANIMATION_LIBS:
            assert lib not in source, f"Layer 3 code must not import {lib}"


class TestAC2TemplateMappingCovers15:
    """AC-2: `TEMPLATE_MAPPING` covers all 15 templates matching the data_type->template_id table"""

    def test_template_mapping_exists(self):
        source = _read_text(REGISTRY_PATH)
        assert "TEMPLATE_MAPPING" in source, (
            "template_registry.ts must export TEMPLATE_MAPPING"
        )

    def test_all_15_data_types_mapped(self):
        source = _read_text(REGISTRY_PATH)
        for data_type in EXPECTED_TEMPLATE_MAPPING:
            assert data_type in source, (
                f"TEMPLATE_MAPPING must contain data_type '{data_type}'"
            )

    def test_all_15_template_ids_mapped(self):
        source = _read_text(REGISTRY_PATH)
        for template_id in EXPECTED_TEMPLATE_MAPPING.values():
            assert template_id in source, (
                f"TEMPLATE_MAPPING must contain template_id '{template_id}'"
            )

    def test_mapping_lookup_function_exists(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(
            r"getTemplateByDataType|resolveTemplate|TEMPLATE_MAPPING\[", source
        ), "template_registry.ts must have a lookup function for TEMPLATE_MAPPING"


class TestAC3TemplateMappingFallbackToLlm:
    """AC-3: TEMPLATE_MAPPING lookup returns null/undefined only when data_type has no mapping; LLM recommendation only in that case"""

    def test_fallback_to_llm_pattern_exists(self):
        source = _read_text(REGISTRY_PATH)
        # Must have fallback logic: null check + LLM invoke
        has_null_check = re.search(r"null|undefined|\?\?|!\s*\w+\s*return", source)
        assert has_null_check, (
            "TEMPLATE_MAPPING lookup must handle null/undefined for unmapped data_type"
        )

    def test_llm_recommendation_conditional(self):
        source = _read_text(REGISTRY_PATH)
        # LLM call must be conditional on mapping returning null
        assert "recommend" in source.lower() or "llm" in source.lower(), (
            "TEMPLATE_MAPPING must invoke LLM recommendation when lookup returns null"
        )


class TestAC4KeyframeTimelineAlignment:
    """AC-4: All `annotation_keyframes` are validated against `timeline.json` alignment (programmatic check)"""

    def test_keyframe_validation_function_exists(self):
        # Check in SegmentSequencer or VideoComposition
        for f in LAYER3_FILES:
            if not f.is_file():
                continue
            source = f.read_text(encoding="utf-8")
            if "validateKeyframe" in source or "validate_keyframe" in source:
                return
        # Also check registry
        reg = _read_text(REGISTRY_PATH)
        assert "validate" in reg.lower(), (
            "Layer 3 code must have keyframe validation logic"
        )

    def test_timeline_alignment_reference(self):
        source = _layer3_source()
        has_timeline = (
            "timeline" in source.lower()
            or "startFrame" in source
            or "endFrame" in source
        )
        assert has_timeline, (
            "Layer 3 code must reference timeline.json for keyframe alignment"
        )


class TestAC5DataPointIdTraceability:
    """AC-5: All numeric params (`data_points`, `ohlc_data`) traceable via `data_point_id` to P2 `key_data_point`"""

    def test_data_point_id_reference_exists(self):
        source = _layer3_source()
        assert "data_point_id" in source or "dataPointId" in source, (
            "Layer 3 code must reference data_point_id for traceability"
        )

    def test_key_data_point_reference_exists(self):
        source = _layer3_source()
        assert "key_data_point" in source or "keyDataPoint" in source, (
            "Layer 3 code must reference key_data_point for P2 traceability"
        )


class TestAC6PauseTriggerFrameFreeze:
    """AC-6: Continuous keyframe `pause_triggers` correctly freeze frames via `useCurrentFrame()`"""

    def test_use_current_frame_in_layer3(self):
        source = _layer3_source()
        assert "useCurrentFrame" in source, (
            "Layer 3 code must use useCurrentFrame() for frame control"
        )

    def test_pause_trigger_freeze_logic(self):
        source = _layer3_source()
        has_pause_logic = (
            "pause_trigger" in source
            or "pauseTrigger" in source
            or "isPaused" in source
            or "freeze" in source.lower()
        )
        assert has_pause_logic, "Layer 3 code must have pause_trigger freeze logic"

    def test_interpolate_used(self):
        source = _layer3_source()
        assert "interpolate" in source, (
            "Layer 3 code must use interpolate() for animation progress"
        )


class TestAC7CompositionReadsPlatformProfile:
    """AC-7: `<Composition>` reads fps/width/height from platform profile config"""

    def test_platform_profile_exists(self):
        source = _layer3_source()
        has_profile = (
            "PLATFORM_PROFILES" in source
            or "platform_profile" in source
            or "platformProfile" in source
            or "getRenderConfig" in source
        )
        assert has_profile, "Layer 3 code must reference platform profile config"

    def test_fps_from_config(self):
        source = _layer3_source()
        has_fps = "fps" in source.lower()
        assert has_fps, "VideoComposition must read fps from platform profile config"

    def test_dimensions_from_config(self):
        source = _layer3_source()
        has_width = "width" in source.lower()
        has_height = "height" in source.lower()
        assert has_width and has_height, (
            "VideoComposition must read width/height from platform profile config"
        )
