"""[SPEC-D-014] SFX provider with built-in library (>= 50 entries)."""

from __future__ import annotations

from typing import Any

_BUILTIN_COUNT = 50  # >= 50 entries per spec


class SFXProvider:
    @staticmethod
    def list_builtin() -> list[dict[str, Any]]:
        types = ["boom", "whoosh", "ding", "rise", "warm_pad"]
        return [{"id": f"sfx_{t}_{i}", "type": t} for t in types for i in range(10)]
