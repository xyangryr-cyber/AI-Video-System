"""Commit a media artifact as a (file, artifact_ref) pair.

Contract (SPEC-B-002):

* The media file on disk is the payload; the DB row is the reference.
* On DB-commit failure the file is orphaned and MUST be removed before
  the error propagates to the caller (AC-2).
* Structured state flows in one direction: DB is the source of truth,
  exported files like ``snapshot.md`` / ``project_state.json`` are
  read-only views and are NOT consulted from the write path (AC-1 /
  AC-3).
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from src.backend.core.storage import MediaStorage


class _PhaseRepoProtocol(Protocol):
    def set_artifact_path(self, project_id: str, phase_num: int, artifact_path: str) -> None: ...


class ArtifactManager:
    def __init__(
        self,
        storage: MediaStorage,
        phase_repo: _PhaseRepoProtocol,
    ) -> None:
        self._storage = storage
        self._phase_repo = phase_repo

    def commit_artifact(
        self,
        project_id: str,
        phase_num: int,
        relative_path: str,
        data: bytes,
    ) -> Path:
        written = self._storage.write_bytes(relative_path, data)
        try:
            self._phase_repo.set_artifact_path(project_id, phase_num, str(written))
        except Exception:
            self._storage.delete(written)
            raise
        return written
