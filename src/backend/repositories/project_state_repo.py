"""Repository for ``projects.master_audio_ref`` ([SPEC-C-016]).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-1
(writer: NarrationMasterAssembler on Gate 4 PASS) plus SPEC-B-013 V006
migration adding the ``master_audio_ref`` TEXT/JSON column.

This lives at ``src/backend/repositories/`` (task-card allowed path)
rather than under ``src/backend/db/repositories/`` because it is the
first writer of a cross-table JSON pointer; follow-on writers
(BgmMixRenderer, FinalAudioAssembler) will share it.

Unlike the auto-commit repositories in ``src/backend/db/repositories``,
this class is transaction-aware: ``set_master_audio_ref`` only issues an
UPDATE and leaves commit/rollback to the caller (the assembler needs to
roll both the DB write and the on-disk master files back together when
something fails mid-flight -- AC-5).
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Mapping
from typing import Any


class ProjectStateRepository:
    """Writes the compact ``master_audio_ref`` pointer on ``projects``."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def set_master_audio_ref(
        self,
        project_id: str,
        ref: Mapping[str, Any],
    ) -> None:
        """UPDATE projects SET master_audio_ref = json(...).

        Does NOT commit; the caller owns the transaction. Raises
        ``KeyError`` if no project row matches ``project_id`` so the
        assembler can bail out before writing master files.
        """
        payload = json.dumps(dict(ref), sort_keys=True)
        cur = self._conn.execute(
            "UPDATE projects "
            "SET master_audio_ref = ?, "
            "    updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
            "WHERE project_id = ?",
            (payload, project_id),
        )
        if cur.rowcount == 0:
            raise KeyError(f"project {project_id!r} not found; cannot set master_audio_ref")

    def get_master_audio_ref(self, project_id: str) -> dict[str, Any] | None:
        """Return the current compact pointer, or None."""
        cur = self._conn.execute(
            "SELECT master_audio_ref FROM projects WHERE project_id = ?",
            (project_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise KeyError(f"project {project_id!r} not found")
        raw = row[0] if not hasattr(row, "keys") else row["master_audio_ref"]
        if raw is None:
            return None
        parsed: dict[str, Any] = json.loads(raw)
        return parsed


__all__ = ["ProjectStateRepository"]
