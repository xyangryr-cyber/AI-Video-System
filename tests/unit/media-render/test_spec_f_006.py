"""Tests for [SPEC-F-006] React Community Components: Event Timeline, Relationship Graph, Map Annotation, Data Card."""

import json
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
FRONTEND_DIR = PROJECT_ROOT / "src" / "frontend"
TEMPLATE_DIR = FRONTEND_DIR / "components" / "templates" / "react"
REGISTRY_PATH = FRONTEND_DIR / "components" / "templates" / "template_registry.ts"
PACKAGE_JSON_PATH = FRONTEND_DIR / "package.json"


def _read_text(path: Path) -> str:
    assert path.is_file(), f"Missing file: {path}"
    return path.read_text(encoding="utf-8")


class TestAC1EventTimelineReactChrono:
    """AC-1: `event_timeline` uses react-chrono ^2.6 + Framer Motion `whileInView` for node pop-in"""

    def test_event_timeline_file_exists(self):
        path = TEMPLATE_DIR / "EventTimeline.tsx"
        assert path.is_file(), f"EventTimeline.tsx not found at {path}"

    def test_event_timeline_imports_react_chrono(self):
        source = _read_text(TEMPLATE_DIR / "EventTimeline.tsx")
        assert re.search(r"from ['\"]react-chrono['\"]", source) or re.search(
            r"react-chrono", source
        ), "EventTimeline.tsx must import from react-chrono"

    def test_event_timeline_has_while_in_view(self):
        source = _read_text(TEMPLATE_DIR / "EventTimeline.tsx")
        assert re.search(r"whileInView", source), (
            "EventTimeline.tsx must use Framer Motion whileInView for node pop-in"
        )


class TestAC2RelationshipGraphNivoPathlength:
    """AC-2: `relationship_graph` uses @nivo/network ^0.87 + SVG `pathLength` for edge draw animation"""

    def test_relationship_graph_file_exists(self):
        path = TEMPLATE_DIR / "RelationshipGraph.tsx"
        assert path.is_file(), f"RelationshipGraph.tsx not found at {path}"

    def test_relationship_graph_imports_nivo(self):
        source = _read_text(TEMPLATE_DIR / "RelationshipGraph.tsx")
        assert re.search(r"from ['\"]@nivo/network['\"]", source) or re.search(
            r"@nivo/network", source
        ), "RelationshipGraph.tsx must import from @nivo/network"

    def test_relationship_graph_has_path_length(self):
        source = _read_text(TEMPLATE_DIR / "RelationshipGraph.tsx")
        assert re.search(r"pathLength", source), (
            "RelationshipGraph.tsx must use SVG pathLength for edge draw animation"
        )


class TestAC3MapAnnotationReactSimpleMaps:
    """AC-3: `map_annotation` uses react-simple-maps ^3.0 + Framer Motion for marker/line/annotation animation"""

    def test_map_annotation_file_exists(self):
        path = TEMPLATE_DIR / "MapAnnotation.tsx"
        assert path.is_file(), f"MapAnnotation.tsx not found at {path}"

    def test_map_annotation_imports_react_simple_maps(self):
        source = _read_text(TEMPLATE_DIR / "MapAnnotation.tsx")
        assert re.search(r"from ['\"]react-simple-maps['\"]", source) or re.search(
            r"react-simple-maps", source
        ), "MapAnnotation.tsx must import from react-simple-maps"

    def test_map_annotation_has_motion(self):
        source = _read_text(TEMPLATE_DIR / "MapAnnotation.tsx")
        assert re.search(r"motion\.", source), (
            "MapAnnotation.tsx must use Framer Motion for marker/line/annotation animation"
        )


class TestAC4DataCardUsespringSparkling:
    """AC-4: `data_card` uses Framer Motion `useSpring` for count animation + ECharts sparkline mini-chart"""

    def test_data_card_file_exists(self):
        path = TEMPLATE_DIR / "DataCard.tsx"
        assert path.is_file(), f"DataCard.tsx not found at {path}"

    def test_data_card_has_use_spring(self):
        source = _read_text(TEMPLATE_DIR / "DataCard.tsx")
        assert re.search(r"useSpring", source), (
            "DataCard.tsx must use Framer Motion useSpring for count animation"
        )

    def test_data_card_has_echarts_or_sparkline(self):
        source = _read_text(TEMPLATE_DIR / "DataCard.tsx")
        assert re.search(r"echarts|ECharts|sparkline", source, re.IGNORECASE), (
            "DataCard.tsx must use ECharts sparkline for mini-chart"
        )


class TestAC5AllImplementTemplateProps:
    """AC-5: All 4 implement `React.FC<TemplateProps>` and are registered in `template_registry.ts`"""

    def test_registry_file_exists(self):
        assert REGISTRY_PATH.is_file(), (
            f"template_registry.ts not found at {REGISTRY_PATH}"
        )

    def test_event_timeline_registered(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(r"EventTimeline", source), (
            "template_registry.ts must reference EventTimeline"
        )

    def test_relationship_graph_registered(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(r"RelationshipGraph", source), (
            "template_registry.ts must reference RelationshipGraph"
        )

    def test_map_annotation_registered(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(r"MapAnnotation", source), (
            "template_registry.ts must reference MapAnnotation"
        )

    def test_data_card_registered(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(r"DataCard", source), (
            "template_registry.ts must reference DataCard"
        )

    def test_template_props_imported(self):
        source = _read_text(REGISTRY_PATH)
        assert re.search(r"TemplateProps", source), (
            "template_registry.ts must import TemplateProps for type annotation"
        )

    def test_all_implement_fc_template_props(self):
        for name in ("EventTimeline", "RelationshipGraph", "MapAnnotation", "DataCard"):
            path = TEMPLATE_DIR / f"{name}.tsx"
            source = _read_text(path)
            assert re.search(r"TemplateProps", source), (
                f"{name}.tsx must reference TemplateProps in its type signature"
            )


class TestAC6DependencyVersionsPinned:
    """AC-6: Community library versions pinned in package.json: react-chrono ^2.6, @nivo/network ^0.87, react-simple-maps ^3.0"""

    def test_react_chrono_pinned(self):
        pkg = json.loads(_read_text(PACKAGE_JSON_PATH))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        version = deps.get("react-chrono", "")
        assert version.startswith("^2.6"), (
            f"react-chrono must be pinned to ^2.6, found: {version}"
        )

    def test_nivo_network_pinned(self):
        pkg = json.loads(_read_text(PACKAGE_JSON_PATH))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        version = deps.get("@nivo/network", "")
        assert version.startswith("^0.87"), (
            f"@nivo/network must be pinned to ^0.87, found: {version}"
        )

    def test_react_simple_maps_pinned(self):
        pkg = json.loads(_read_text(PACKAGE_JSON_PATH))
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        version = deps.get("react-simple-maps", "")
        assert version.startswith("^3.0"), (
            f"react-simple-maps must be pinned to ^3.0, found: {version}"
        )
