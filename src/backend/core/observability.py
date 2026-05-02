"""Four-type observability evidence access (SPEC-B-010).

Provides unified read access to the four evidence types:
1. System status (pre-flight check results)
2. Events (phase transitions, task lifecycle)
3. LLM audit (agent_call_log)
4. Artifacts (phases with artifact_path)
"""

from __future__ import annotations

import sqlite3
from typing import Any


class Observability:
    """Read-only observability queries over the project DB."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def get_system_status(self) -> list[dict[str, Any]]:
        rows = self._conn.execute("SELECT * FROM system_status ORDER BY checked_at DESC").fetchall()
        return [dict(r) for r in rows]

    def get_events(self, project_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM events WHERE project_id = ? ORDER BY timestamp DESC LIMIT ?",
            (project_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_llm_audit(self, project_id: str, limit: int = 100) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM agent_call_log WHERE project_id = ? ORDER BY created_at DESC LIMIT ?",
            (project_id, limit),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_artifacts(self, project_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM phases WHERE project_id = ? "
            "AND artifact_path IS NOT NULL "
            "ORDER BY phase_num ASC",
            (project_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def check_phase_consistency(self, project_id: str) -> dict[str, Any]:
        """Compare projects.current_phase with latest phase.entered event."""
        proj_row = self._conn.execute(
            "SELECT current_phase FROM projects WHERE project_id = ?",
            (project_id,),
        ).fetchone()
        event_row = self._conn.execute(
            "SELECT payload FROM events "
            "WHERE project_id = ? AND type = 'phase.entered' "
            "ORDER BY id DESC LIMIT 1",
            (project_id,),
        ).fetchone()

        current_phase = proj_row["current_phase"] if proj_row else 0
        latest_event_phase = None
        if event_row:
            import json

            try:
                payload = json.loads(event_row["payload"])
                latest_event_phase = payload.get("phase_num")
            except (json.JSONDecodeError, TypeError):
                pass

        return {
            "project_id": project_id,
            "current_phase": current_phase,
            "latest_event_phase": latest_event_phase,
            "consistent": current_phase == latest_event_phase,
        }
