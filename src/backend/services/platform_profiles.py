"""[SPEC-D-009] PlatformProfiles -- multi-platform encoding profiles.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.11.3
"""

from __future__ import annotations

from typing import Any

_PROFILES: dict[str, dict[str, Any]] = {
    "web": {"resolution": "1920x1080", "codec": "h264", "bitrate": "8M"},
    "mobile": {"resolution": "720x1280", "codec": "h264", "bitrate": "4M"},
    "social": {"resolution": "1080x1080", "codec": "h264", "bitrate": "6M"},
}


class PlatformProfiles:
    """Look up encoding profiles by platform name."""

    @staticmethod
    def get_profile(platform: str) -> dict[str, Any]:
        return dict(_PROFILES.get(platform, _PROFILES["web"]))
