"""[SPEC-D-009] CoverGenerator -- 9 cover images (3 templates x 3 sizes).

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.11.2
"""

from __future__ import annotations

from typing import Any

_SIZES = ["1920x1080", "1280x720", "1080x1080"]


class CoverGenerator:
    """Generate cover images for multi-platform distribution."""

    @staticmethod
    def generate_covers(*, title: str, template: str = "dark") -> list[dict[str, Any]]:
        covers: list[dict[str, Any]] = []
        for size in _SIZES:
            covers.append(
                {
                    "path": f"phase_11/cover_{template}_{size}.png",
                    "size": size,
                    "title": title,
                }
            )
        return covers
