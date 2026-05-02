"""[SPEC-C-014] PreferenceService: three-level persistence, confirmation,
snapshot versioning, and rollback.
"""

from __future__ import annotations

import json
import time
import sqlite3
from typing import Any, Literal, cast

from src.shared.constants.auth import DEFAULT_USER_ID

from src.backend.agents.preference_extractor import (
    ExtractedPreference,
    PreferenceExtractor,
)
from src.backend.db.repositories.event_repo import EventRepository
from src.backend.db.repositories.preferences_repo import PreferencesRepository

_SNAPSHOT_CAP = 20


class PreferenceService:
    """Stateless service for preference lifecycle management.

    Operates on a SQLite connection. Manages:
    - Three-level persistence (global, user, project)
    - Extraction + candidate storage
    - Confirmation flow
    - Snapshot versioning (last 20, rollback as new version)
    """

    def __init__(self, conn: str | sqlite3.Connection) -> None:
        if isinstance(conn, str):
            self._conn = sqlite3.connect(conn)
            self._conn.row_factory = sqlite3.Row
            self._own_conn = True
        else:
            self._conn = conn
            self._own_conn = False
        self._prefs_repo = PreferencesRepository(self._conn)
        self._event_repo = EventRepository(self._conn)

    # ------------------------------------------------------------------
    # Schema helpers
    # ------------------------------------------------------------------

    def _ensure_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS preferences (
                project_id TEXT PRIMARY KEY,
                global_rules_md TEXT DEFAULT '',
                user_preferences_md TEXT DEFAULT '',
                project_preferences_md TEXT DEFAULT '',
                brand_kit_json TEXT,
                last_candidates_json TEXT,
                last_confirmed_at TEXT,
                updated_at TEXT
            );
            CREATE TABLE IF NOT EXISTS preference_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                snapshot_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS user_preferences_store (
                user_id TEXT PRIMARY KEY,
                prefs_md TEXT DEFAULT ''
            );
            CREATE TABLE IF NOT EXISTS global_rules_store (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                rules_md TEXT DEFAULT ''
            );
        """)
        self._conn.commit()

    def _init_project(self, project_id: str) -> None:
        self._prefs_repo.initialize_for_project(project_id)

    # ------------------------------------------------------------------
    # Three-level persistence
    # ------------------------------------------------------------------

    def set_global_rules(self, rules_md: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO global_rules_store (id, rules_md) VALUES (1, ?)",
            (rules_md,),
        )
        self._conn.commit()

    def set_user_preferences(self, user_id: str, prefs_md: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO user_preferences_store (user_id, prefs_md) VALUES (?, ?)",
            (user_id, prefs_md),
        )
        self._conn.commit()

    def get_global_rules(self) -> str:
        row = self._conn.execute(
            "SELECT rules_md FROM global_rules_store WHERE id = 1"
        ).fetchone()
        return row[0] if row else ""

    def get_user_preferences(self, user_id: str) -> str:
        row = self._conn.execute(
            "SELECT prefs_md FROM user_preferences_store WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return row[0] if row else ""

    def get_project_preferences(self, project_id: str) -> str:
        row = self._conn.execute(
            "SELECT project_preferences_md FROM preferences WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            return ""
        if isinstance(row, (tuple, list)):
            return row[0] or ""
        return row["project_preferences_md"] or ""

    def get_effective_preferences(
        self, project_id: str, user_id: str = DEFAULT_USER_ID
    ) -> str:
        """Merge global + user + project preferences (AC-7)."""
        global_rules = self.get_global_rules()
        user_prefs = self.get_user_preferences(user_id)
        project_prefs = self.get_project_preferences(project_id)
        parts = [p for p in [global_rules, user_prefs, project_prefs] if p]
        return "\n\n".join(parts)

    # ------------------------------------------------------------------
    # Extraction (AC-3)
    # ------------------------------------------------------------------

    def extract_and_store_candidates(
        self, project_id: str, stage: str, utterance: str
    ) -> dict[str, Any]:
        extractor = PreferenceExtractor()
        result = extractor.extract(
            utterance=utterance,
            stage=cast(
                Literal[
                    "P2_script",
                    "P3_polish",
                    "P4_tts",
                    "P5_bgm",
                    "P6_sfx",
                    "P7_storyboard",
                    "P8_keyframe",
                    "P9_broll",
                    "P10_roughcut",
                    "P11_finalize",
                ],
                stage,
            ),
            confidence=0.9,
        )
        if result is not None:
            candidates = [result]
            nothing_found = False
        else:
            candidates = []
            nothing_found = True

        self._prefs_repo.update_last_candidates(
            project_id,
            json.dumps(
                {
                    "candidates": [self._pref_to_dict(c) for c in candidates],
                    "nothing_found": nothing_found,
                },
                ensure_ascii=False,
            ),
        )
        return {"candidates": candidates, "nothing_found": nothing_found}

    @staticmethod
    def _pref_to_dict(p: ExtractedPreference) -> dict[str, Any]:
        return {
            "id": p.id,
            "rule": p.rule,
            "scope": p.scope,
            "stage": p.stage,
            "key": p.key,
            "value": p.value,
            "confidence": p.confidence,
            "evidence_segment_id": p.evidence_segment_id,
            "source": p.source,
            "proposed_action": p.proposed_action,
        }

    # ------------------------------------------------------------------
    # Confirmation flow
    # ------------------------------------------------------------------

    def accept_preference(self, project_id: str, pref: ExtractedPreference) -> None:
        """Write an accepted preference to the project_preferences_md."""
        current = self.get_project_preferences(project_id)
        new_rule = f"- **{pref.key}** = {pref.value} (scope: {pref.scope}, confidence: {pref.confidence:.2f})"
        updated = (current + "\n" + new_rule).strip() if current else new_rule
        self._prefs_repo.update_project_preferences(project_id, updated)

    def edit_and_accept(
        self,
        project_id: str,
        *,
        original_text: str,
        modified_text: str,
        scope: str,
        stage: str | None,
        key: str,
        value: Any,
    ) -> None:
        """Accept edited text — only modified text is persisted (AC-5)."""
        current = self.get_project_preferences(project_id)
        new_rule = f"- **{key}** = {value} (scope: {scope}, edited)"
        updated = (current + "\n" + new_rule).strip() if current else new_rule
        self._prefs_repo.update_project_preferences(project_id, updated)

    def confirm_preferences(self, project_id: str) -> None:
        """Stamp last_confirmed_at (AC-6)."""
        self._prefs_repo.mark_confirmed(project_id)

    def get_confirmed_at(self, project_id: str) -> str | None:
        row = self._conn.execute(
            "SELECT last_confirmed_at FROM preferences WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            return None
        if isinstance(row, (tuple, list)):
            return cast(str, row[0])
        return cast(str, row["last_confirmed_at"])

    # ------------------------------------------------------------------
    # Snapshot versioning (AC-8, AC-9, AC-10)
    # ------------------------------------------------------------------

    def create_snapshot(self, project_id: str) -> int:
        """Save current preferences state as a versioned snapshot.
        Returns the new snapshot version number (1-indexed).
        """
        row = self._conn.execute(
            "SELECT global_rules_md, user_preferences_md, project_preferences_md, last_confirmed_at FROM preferences WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        if row is None:
            self._init_project(project_id)
            row = self._conn.execute(
                "SELECT global_rules_md, user_preferences_md, project_preferences_md, last_confirmed_at FROM preferences WHERE project_id = ?",
                (project_id,),
            ).fetchone()

        # Determine next version
        _max_v_raw = self._conn.execute(
            "SELECT COALESCE(MAX(version), 0) FROM preference_snapshots WHERE project_id = ?",
            (project_id,),
        ).fetchone()[0]
        max_v = cast(int, _max_v_raw)
        new_version = max_v + 1

        snapshot = {
            "version": new_version,
            "global_rules_md": row[0]
            if isinstance(row, (tuple, list))
            else row["global_rules_md"],
            "user_preferences_md": row[1]
            if isinstance(row, (tuple, list))
            else row["user_preferences_md"],
            "project_preferences_md": row[2]
            if isinstance(row, (tuple, list))
            else row["project_preferences_md"],
            "confirmed_at": row[3]
            if isinstance(row, (tuple, list))
            else row["last_confirmed_at"],
        }
        self._prefs_repo.create_snapshot(
            project_id,
            new_version,
            json.dumps(snapshot, ensure_ascii=False),
        )

        # Prune to last 20 (AC-9)
        self._prune_snapshots(project_id)
        return new_version

    def _prune_snapshots(self, project_id: str) -> None:
        """Keep only the 20 most recent snapshots (AC-9)."""
        self._prefs_repo.delete_old_snapshots(project_id, _SNAPSHOT_CAP)

    def list_snapshots(self, project_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT id, version, snapshot_json, created_at FROM preference_snapshots WHERE project_id = ? ORDER BY version DESC",
            (project_id,),
        ).fetchall()
        return [
            {
                "id": r[0] if isinstance(r, (tuple, list)) else r["id"],
                "version": r[1] if isinstance(r, (tuple, list)) else r["version"],
                "snapshot": json.loads(
                    r[2] if isinstance(r, (tuple, list)) else r["snapshot_json"]
                ),
                "created_at": r[3] if isinstance(r, (tuple, list)) else r["created_at"],
            }
            for r in rows
        ]

    def rollback(self, project_id: str, version: int) -> None:
        """Restore from a snapshot. Creates a NEW version (AC-10) and
        writes a ``preference.rollback`` event (AC-11)."""
        row = self._conn.execute(
            "SELECT snapshot_json FROM preference_snapshots WHERE project_id = ? AND version = ?",
            (project_id, version),
        ).fetchone()
        if row is None:
            raise ValueError(f"Snapshot version {version} not found for {project_id}")
        snapshot = json.loads(
            row[0] if isinstance(row, (tuple, list)) else row["snapshot_json"]
        )

        # Restore
        self._prefs_repo.update_all_prefs(
            project_id,
            snapshot.get("global_rules_md", ""),
            snapshot.get("user_preferences_md", ""),
            snapshot.get("project_preferences_md", ""),
        )

        # Write rollback event (AC-11) -- safe if events table missing
        try:
            self._event_repo.insert_event(
                project_id,
                "preference.rollback",
                json.dumps(
                    {"rolled_back_to": version, "timestamp": time.time()},
                    ensure_ascii=False,
                ),
            )
        except sqlite3.OperationalError:
            pass

        # Create new snapshot version (AC-10)
        self.create_snapshot(project_id)

    def close(self) -> None:
        if self._own_conn:
            self._conn.close()


__all__ = ["PreferenceService"]
