"""[SPEC-D-014] BGM provider with local library."""

from __future__ import annotations

from typing import Any, Dict


class BGMProvider:
    @staticmethod
    def fetch(*, emotion: str, energy: int) -> Dict[str, Any]:
        return {"track_id": f"local_{emotion}_01", "source": "local_library"}
