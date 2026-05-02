"""[SPEC-D-014] MaterialFallback -- multi-level fallback for SFX/BGM/B-Roll."""

from __future__ import annotations

from typing import Any, Dict

from src.backend.services.material_providers.bgm_provider import BGMProvider
from src.backend.services.material_providers.broll_provider import BRollProvider
from src.backend.services.material_providers.sfx_provider import SFXProvider


class MaterialFallback:
    """Material supply chain with fallback chains and offline mode."""

    is_offline_mode = False

    def __init__(self) -> None:
        self._sfx = SFXProvider()
        self._bgm = BGMProvider()
        self._broll = BRollProvider()

    def fetch_sfx(self, *, sfx_type: str, source: str = "builtin") -> Dict[str, Any]:
        builtin = self._sfx.list_builtin()
        found = [s for s in builtin if s["type"] == sfx_type]
        if found:
            return {
                "source_used": "builtin",
                "file_path": f"builtin/{found[0]['id']}.wav",
            }
        if source == "freesound":
            return {
                "source_used": "freesound",
                "license": "CC0",
                "file_path": f"freesound/{sfx_type}.wav",
            }
        return {"source_used": "user_upload", "file_path": f"uploads/{sfx_type}.wav"}

    def fetch_bgm(self, *, emotion: str, energy: int) -> Dict[str, Any]:
        # Mubert API -> local library (2-level)
        # Stub: Mubert unavailable, fall through to local
        result = self._bgm.fetch(emotion=emotion, energy=energy)
        result["source_attempted"] = "mubert_api"
        result["reason_failed"] = "API unavailable (stub)"
        result["source_used"] = result.get("source", "local_library")
        return result

    def fetch_broll(self, *, query: str) -> Dict[str, Any]:
        return self._broll.fetch(query=query)
