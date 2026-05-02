"""[SPEC-D-007] RenderEngineSelector -- 3-layer architecture engine routing.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.8.3
"""

from __future__ import annotations

_ENGINE_MAP = {
    "chart_card": "echarts",
    "data_table": "react",
    "title_card": "react",
    "comparison_card": "echarts",
    "text_card": "react",
    "animation": "remotion",
}


class RenderEngineSelector:
    """Route template_type to ECharts / React / Remotion engine."""

    @staticmethod
    def select(*, template_type: str) -> str:
        return _ENGINE_MAP.get(template_type, "react")
