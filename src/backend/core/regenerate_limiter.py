"""Regenerate limiter (SPEC-B-012 AC-2).

After max_regenerates consecutive calls on the same section,
returns suggest_manual_edit=true to nudge the user toward manual editing.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any


class RegenerateLimiter:
    def __init__(self, max_regenerates: int = 5) -> None:
        self._max = max_regenerates
        self._counts: dict[str, int] = defaultdict(int)

    def check(self, section_id: str) -> dict[str, Any]:
        """Increment the regenerate counter for section_id and return
        {suggest_manual_edit, remaining, count}.
        """
        self._counts[section_id] += 1
        count = self._counts[section_id]
        remaining = max(0, self._max - count)
        return {
            "section_id": section_id,
            "count": count,
            "remaining": remaining,
            "suggest_manual_edit": count >= self._max,
        }

    def reset(self, section_id: str) -> None:
        self._counts.pop(section_id, None)
