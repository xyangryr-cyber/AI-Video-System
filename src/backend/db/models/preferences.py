"""Pydantic model for ``preferences`` rows (SPEC-B-006 / SPEC-12.1).

Mirrors the DDL in ``src/backend/db/schema.sql`` so API / repository
callers use a typed object instead of raw ``sqlite3.Row``. The table
has exactly one row per project (PRIMARY KEY = project_id).
"""

from __future__ import annotations

from pydantic import BaseModel


class Preferences(BaseModel):
    project_id: str
    global_rules_md: str = ""
    user_preferences_md: str = ""
    project_preferences_md: str = ""
    brand_kit_json: str | None = None
    last_candidates_json: str | None = None
    last_confirmed_at: str | None = None
    updated_at: str
