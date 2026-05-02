"""[RED] Tests for new PreferencesRepository methods before they exist."""

import json
import sqlite3
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
SCHEMA_FILE = REPO_ROOT / "src" / "backend" / "db" / "schema.sql"


@pytest.fixture
def conn() -> sqlite3.Connection:
    c = sqlite3.connect(":memory:", check_same_thread=False)
    c.row_factory = sqlite3.Row
    c.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))
    # Recreate preference_snapshots with the runtime schema (version + snapshot_json)
    # used by PreferenceService._ensure_tables()
    c.execute("DROP TABLE IF EXISTS preference_snapshots")
    c.execute(
        "CREATE TABLE preference_snapshots ("
        "  id INTEGER PRIMARY KEY AUTOINCREMENT,"
        "  project_id TEXT NOT NULL,"
        "  version INTEGER NOT NULL,"
        "  snapshot_json TEXT NOT NULL,"
        "  created_at TEXT NOT NULL"
        ")"
    )
    c.execute(
        "INSERT INTO projects(project_id, title, description) "
        "VALUES ('proj_t', 'T', 'D')"
    )
    c.commit()
    return c


class TestPreferencesRepoUpdateLastCandidates:
    """RED: update_last_candidates writes last_candidates_json and bumps updated_at."""

    def test_update_last_candidates(self, conn):
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        repo = PreferencesRepository(conn)
        repo.initialize_for_project("proj_t")

        candidates = json.dumps({"candidates": [], "nothing_found": True})
        repo.update_last_candidates("proj_t", candidates)

        row = conn.execute(
            "SELECT last_candidates_json, updated_at FROM preferences WHERE project_id = 'proj_t'"
        ).fetchone()
        assert row is not None
        assert row["last_candidates_json"] == candidates
        assert row["updated_at"] is not None


class TestPreferencesRepoUpdateProjectPreferences:
    """RED: update_project_preferences writes project_preferences_md."""

    def test_update_project_preferences(self, conn):
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        repo = PreferencesRepository(conn)
        repo.initialize_for_project("proj_t")

        repo.update_project_preferences("proj_t", "- **key** = value")

        row = conn.execute(
            "SELECT project_preferences_md FROM preferences WHERE project_id = 'proj_t'"
        ).fetchone()
        assert row["project_preferences_md"] == "- **key** = value"


class TestPreferencesRepoCreateSnapshot:
    """RED: create_snapshot inserts into preference_snapshots."""

    def test_create_snapshot(self, conn):
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        repo = PreferencesRepository(conn)
        repo.initialize_for_project("proj_t")

        snap = json.dumps({"version": 1, "global_rules_md": "rules"})
        repo.create_snapshot("proj_t", 1, snap)

        row = conn.execute(
            "SELECT version, snapshot_json FROM preference_snapshots WHERE project_id = 'proj_t'"
        ).fetchone()
        assert row is not None
        assert row["version"] == 1
        assert row["snapshot_json"] == snap


class TestPreferencesRepoDeleteOldSnapshots:
    """RED: delete_old_snapshots keeps only the N most recent versions."""

    def test_delete_old_snapshots_keeps_N(self, conn):
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        repo = PreferencesRepository(conn)
        repo.initialize_for_project("proj_t")

        for v in range(1, 6):
            repo.create_snapshot("proj_t", v, json.dumps({"version": v}))

        repo.delete_old_snapshots("proj_t", 3)

        rows = conn.execute(
            "SELECT version FROM preference_snapshots WHERE project_id = 'proj_t' ORDER BY version DESC"
        ).fetchall()
        assert len(rows) == 3
        versions = [r["version"] for r in rows]
        assert versions == [5, 4, 3]


class TestPreferencesRepoUpdateAllPrefs:
    """RED: update_all_prefs writes all three MD fields."""

    def test_update_all_prefs(self, conn):
        from src.backend.db.repositories.preferences_repo import (
            PreferencesRepository,
        )

        repo = PreferencesRepository(conn)
        repo.initialize_for_project("proj_t")

        repo.update_all_prefs("proj_t", "g", "u", "p")

        row = conn.execute(
            "SELECT global_rules_md, user_preferences_md, project_preferences_md "
            "FROM preferences WHERE project_id = 'proj_t'"
        ).fetchone()
        assert row["global_rules_md"] == "g"
        assert row["user_preferences_md"] == "u"
        assert row["project_preferences_md"] == "p"


class TestEventRepository:
    """RED: EventRepository.insert_event inserts into events table."""

    def test_insert_event(self, conn):
        from src.backend.db.repositories.event_repo import EventRepository

        repo = EventRepository(conn)
        repo.insert_event("proj_t", "preference.rollback", '{"rolled_back_to": 1}')

        row = conn.execute(
            "SELECT project_id, type, payload FROM events WHERE project_id = 'proj_t'"
        ).fetchone()
        assert row is not None
        assert row["project_id"] == "proj_t"
        assert row["type"] == "preference.rollback"
        assert row["payload"] == '{"rolled_back_to": 1}'
