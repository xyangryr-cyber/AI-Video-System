"""CRUD for ``preferences`` (SPEC-B-006 / SPEC-12.1, SPEC-12.2).

SQLite is the single source of truth for preferences. The two files
``snapshot.md`` / ``project_state.json`` are read-only export views
(dump targets) and MUST NOT be written back into this table -- see
SPEC-12.2.

Writers land here. The public surface is:

* ``initialize_for_project(project_id)`` -- auto-insert on project
  creation (AC-1). Idempotent via INSERT OR IGNORE so repeated creates
  (or replay after crash) are safe.
* ``get(project_id)`` -- read the row (frontend uses the API wrapper).
* ``update(project_id, ...)`` -- partial update of the markdown fields
  and JSON blobs; bumps ``updated_at``.
* ``mark_confirmed(project_id)`` -- stamps ``last_confirmed_at`` to
  satisfy SPEC-12.1 AC-2.
"""

from __future__ import annotations

import sqlite3
from typing import Optional, cast

from src.backend.db.repositories.base import BaseRepository


class PreferencesRepository(BaseRepository):
    def initialize_for_project(self, project_id: str) -> None:
        """Insert the empty preferences row for a newly-created project.

        Idempotent: ``INSERT OR IGNORE`` short-circuits if a row
        already exists (PK = project_id), so callers can invoke this
        unconditionally after ``INSERT INTO projects``.
        """
        self.execute(
            "INSERT OR IGNORE INTO preferences (project_id) VALUES (?)",
            (project_id,),
        )
        self.commit()

    def get(self, project_id: str) -> sqlite3.Row | None:
        cur = self.execute(
            "SELECT * FROM preferences WHERE project_id = ?",
            (project_id,),
        )
        return cast(sqlite3.Row | None, cur.fetchone())

    def update(
        self,
        project_id: str,
        *,
        global_rules_md: Optional[str] = None,
        user_preferences_md: Optional[str] = None,
        project_preferences_md: Optional[str] = None,
        brand_kit_json: Optional[str] = None,
        last_candidates_json: Optional[str] = None,
    ) -> None:
        """Partial update -- only the fields explicitly supplied are
        overwritten. Bumps ``updated_at`` to now."""
        sets: list[str] = []
        params: list[object] = []
        if global_rules_md is not None:
            sets.append("global_rules_md = ?")
            params.append(global_rules_md)
        if user_preferences_md is not None:
            sets.append("user_preferences_md = ?")
            params.append(user_preferences_md)
        if project_preferences_md is not None:
            sets.append("project_preferences_md = ?")
            params.append(project_preferences_md)
        if brand_kit_json is not None:
            sets.append("brand_kit_json = ?")
            params.append(brand_kit_json)
        if last_candidates_json is not None:
            sets.append("last_candidates_json = ?")
            params.append(last_candidates_json)
        if not sets:
            return
        sets.append("updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now')")
        sql = "UPDATE preferences SET " + ", ".join(sets) + " WHERE project_id = ?"
        params.append(project_id)
        self.execute(sql, tuple(params))
        self.commit()

    def mark_confirmed(self, project_id: str) -> None:
        """Stamp ``last_confirmed_at`` = now (SPEC-12.1 AC-2).

        Also bumps ``updated_at`` so downstream consumers watching
        change timestamps pick the event up.
        """
        self.execute(
            "UPDATE preferences "
            "SET last_confirmed_at = strftime('%Y-%m-%dT%H:%M:%fZ','now'), "
            "    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE project_id = ?",
            (project_id,),
        )
        self.commit()

    # -- Convenience methods for PreferenceService (SPEC-B-002 AC-4) -------

    def update_last_candidates(self, project_id: str, candidates_json: str) -> None:
        """Write extracted-for-review candidates JSON."""
        self.update(project_id, last_candidates_json=candidates_json)

    def update_project_preferences(self, project_id: str, prefs_md: str) -> None:
        """Write the project-level preferences markdown blob."""
        self.update(project_id, project_preferences_md=prefs_md)

    def create_snapshot(
        self, project_id: str, version: int, snapshot_json: str
    ) -> None:
        """Insert a single versioned snapshot row."""
        self.execute(
            "INSERT INTO preference_snapshots "
            "(project_id, version, snapshot_json, created_at) "
            "VALUES (?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ','now'))",
            (project_id, version, snapshot_json),
        )
        self.commit()

    def delete_old_snapshots(self, project_id: str, keep_count: int) -> None:
        """Keep only the *keep_count* most-recent snapshots for a project."""
        self.execute(
            "DELETE FROM preference_snapshots "
            "WHERE id NOT IN ("
            "  SELECT id FROM preference_snapshots "
            "  WHERE project_id = ? "
            "  ORDER BY version DESC LIMIT ?"
            ") AND project_id = ?",
            (project_id, keep_count, project_id),
        )
        self.commit()

    def update_all_prefs(
        self,
        project_id: str,
        global_rules_md: str,
        user_preferences_md: str,
        project_preferences_md: str,
    ) -> None:
        """Atomically overwrite all three markdown preference columns."""
        self.update(
            project_id,
            global_rules_md=global_rules_md,
            user_preferences_md=user_preferences_md,
            project_preferences_md=project_preferences_md,
        )
