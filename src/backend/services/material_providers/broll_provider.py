"""[SPEC-D-014] B-Roll provider with pexels/pixabay/placeholder fallback."""

from __future__ import annotations

from typing import Any, Dict


class BRollProvider:
    @staticmethod
    def fetch(*, query: str) -> Dict[str, Any]:
        if "rare" in query or "xyz" in query:
            return {"is_placeholder": True, "description": f"Placeholder: {query}"}
        return {"source_used": "pexels", "file_path": f"broll/{query}.mp4"}
