"""GET /api/projects/{project_id}/preferences (SPEC-B-006 / SPEC-12.2).

Single read path for project preferences. The API reads from SQLite
ONLY -- ``snapshot.md`` and ``project_state.json`` are read-only
export views and are never consulted here. This is the invariant
SPEC-12.2 AC-1 exercises (modifying snapshot.md must not move the
API return value).
"""

from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from src.backend.db.repositories.preferences_repo import (
    PreferencesRepository,
)

router = APIRouter(prefix="/api", tags=["preferences"])


def get_db() -> sqlite3.Connection:  # pragma: no cover -- app wiring
    """Overridden via ``app.dependency_overrides[get_db]`` in tests
    and by the production startup hook."""
    raise RuntimeError(
        "DB dependency not wired. Override get_db in the app startup hook or in tests."
    )


def _serialize(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "project_id": row["project_id"],
        "global_rules_md": row["global_rules_md"],
        "user_preferences_md": row["user_preferences_md"],
        "project_preferences_md": row["project_preferences_md"],
        "brand_kit_json": row["brand_kit_json"],
        "last_candidates_json": row["last_candidates_json"],
        "last_confirmed_at": row["last_confirmed_at"],
        "updated_at": row["updated_at"],
    }


@router.get("/projects/{project_id}/preferences")
def get_project_preferences(
    project_id: str,
    db: sqlite3.Connection = Depends(get_db),
) -> dict[str, Any]:
    repo = PreferencesRepository(db)
    row = repo.get(project_id)
    if row is None:
        raise HTTPException(status_code=404, detail="preferences not found")
    return _serialize(row)
