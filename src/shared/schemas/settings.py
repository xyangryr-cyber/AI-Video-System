"""Settings, Preferences & Snapshot API schemas (SPEC-0A.4).

Encodes:
  - SettingsResponse      → GET /api/settings
  - PreferencesResponse   → GET /api/settings/preferences
  - PreferencesUpdateRequest → PUT /api/settings/preferences
  - SnapshotItem / SnapshotListResponse → GET /api/settings/preferences/snapshots
  - PREFERENCE_WRITE_FLOW     → AC-7 documented flow invariants
  - PREFERENCE_ROLLBACK_FLOW  → AC-8 documented flow invariants
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from src.shared.schemas.brand_kit import BrandKit  # noqa: E402


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class SettingsResponse(_Strict):
    model_config_data: dict[str, Any]
    brand_kit: BrandKit


class PreferencesResponse(_Strict):
    global_rules_md: str
    user_preferences_md: str


class PreferencesUpdateRequest(_Strict):
    global_rules_md: str | None = None
    user_preferences_md: str | None = None


class SnapshotItem(_Strict):
    id: str
    created_at: str
    preview: str


class SnapshotListResponse(_Strict):
    snapshots: list[SnapshotItem]


# AC-7: Preference write flow invariants (documentation-as-code).
# Callers: API layer for PUT /api/settings/preferences.
PREFERENCE_WRITE_FLOW: dict[str, Any] = {
    "snapshot_before_update": True,
    "steps": [
        "1. Create snapshot of current preferences into preference_snapshots table",
        "2. Update preferences table fields (global_rules_md / user_preferences_md)",
        "3. Return snapshot_id of the newly created snapshot",
    ],
    "returns": ["ok", "snapshot_id"],
}

# AC-8: Preference rollback flow invariants (documentation-as-code).
# Callers: API layer for POST /api/settings/preferences/snapshots/{id}/rollback.
PREFERENCE_ROLLBACK_FLOW: dict[str, Any] = {
    "snapshot_current": True,
    "overwrite_from_target": True,
    "audit_event": "preference.rollback",
    "steps": [
        "1. Create snapshot of current preferences (rollback also produces a version record)",
        "2. Overwrite preferences table from target snapshot content",
        "3. Write audit event (type=preference.rollback) to events table",
        "4. Return new_snapshot_id of the snapshot created in step 1",
    ],
    "returns": ["ok", "new_snapshot_id"],
}


__all__ = [
    "PREFERENCE_ROLLBACK_FLOW",
    "PREFERENCE_WRITE_FLOW",
    "PreferencesResponse",
    "PreferencesUpdateRequest",
    "SettingsResponse",
    "SnapshotItem",
    "SnapshotListResponse",
]
