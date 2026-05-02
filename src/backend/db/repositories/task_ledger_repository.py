"""Repository for task_ledger table writes."""

from __future__ import annotations

from src.backend.db.repositories.base import BaseRepository


class TaskLedgerRepository(BaseRepository):
    def update_result_ref(self, task_id: str, result_ref: str) -> None:
        self.execute(
            "UPDATE task_ledger SET result_ref = ? WHERE id = ?",
            (result_ref, task_id),
        )
        self.commit()
