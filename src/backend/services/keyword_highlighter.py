"""[SPEC-D-008] P10 KeywordHighlighter -- highlight financial keywords in subtitles.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.10.4
"""

from __future__ import annotations

from typing import Any


class KeywordHighlighter:
    """Apply keyword highlighting to subtitle entries."""

    @staticmethod
    def highlight(*, subtitles: list[dict[str, Any]], keywords: list[str]) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []
        for sub in subtitles:
            text = sub.get("text", "")
            highlighted = any(kw in text for kw in keywords)
            result.append({**sub, "highlighted": highlighted})
        return result
