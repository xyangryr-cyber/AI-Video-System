"""Repository for events table writes."""

from __future__ import annotations

from src.backend.db.repositories.base import BaseRepository


class EventRepository(BaseRepository):
    def insert_event(self, project_id: str, event_type: str, payload_json: str) -> None:
        self.execute(
            "INSERT INTO events (project_id, type, payload) VALUES (?, ?, ?)",
            (project_id, event_type, payload_json),
        )
        self.commit()
