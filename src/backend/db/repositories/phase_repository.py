"""Phase row writes -- owner of ``phases.artifact_path`` updates.

Part of SPEC-B-002's centralization of DB writes: callers committing
a media artifact to a phase go through this repository rather than
issuing ad-hoc UPDATEs in services or agents.
"""

from __future__ import annotations

from src.backend.db.repositories.base import BaseRepository


class PhaseRepository(BaseRepository):
    def set_artifact_path(
        self,
        project_id: str,
        phase_num: int,
        artifact_path: str,
    ) -> None:
        self.execute(
            "UPDATE phases SET artifact_path = ?, "
            "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE project_id = ? AND phase_num = ?",
            (artifact_path, project_id, phase_num),
        )
        self.commit()
