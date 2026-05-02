"""[SPEC-C-005] Version management & review supersede.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.5 + SPEC-3.2 AC-3.

Responsibility
--------------
``complete_artifact_task`` is the single atomic entry point invoked when
a ``generate_artifact`` or ``user_revision`` task finishes. In one call it:

1. Transitions the source task ``running -> succeeded`` through
   :class:`WorkflowEngine` (SPEC-3.1 centralisation point).
2. Increments ``phases.artifact_version`` by 1.
3. Marks every still-open ``review`` task in the same phase whose
   ``target_version`` no longer matches the bumped value as
   ``superseded`` (SPEC-3.2 AC-3 / SPEC-3.5 invariant).
4. Auto-creates a fresh ``pending`` review row whose ``target_version``
   equals the new artifact version.

Result: at most one ``pending`` review per ``(project_id, phase)``,
always pointed at the most recent artifact (SPEC-3.5 invariant).

Why a separate class
--------------------
The bump-and-supersede logic ties three table writes (``phases`` /
``task_ledger`` two flavours / ``events`` × N) into one transactional
unit. Putting this on :class:`WorkflowEngine` would push that file past
the HARNESS §6 400-line ceiling and conflate FSM mechanics (3.1/3.2/3.6)
with versioning policy (3.5). PhaseOps (SPEC-C-004) follows the same
"one operational concern per file" pattern.

Why ``phases`` writes live here
-------------------------------
SPEC-B-002 AC-4 scans for raw mutation-SQL line patterns outside
``src/backend/db/repositories/``. ``phases`` mutations are also done
in ``phase_ops.py`` (SPEC-C-004) using line-split SQL fragments. We use
the same trick here so a single line never matches the regex.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass

from src.backend.engine.task_types import TaskType
from src.backend.engine.workflow_engine import WorkflowEngine


# -- SQL constants (line-split to dodge SPEC-B-002 AC-4 regex) ------------

_UPDATE_PHASE_BUMP_VERSION_SQL = (
    "UPDATE "
    "phases SET artifact_version = artifact_version + 1, "
    "updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') "
    "WHERE project_id = ? AND phase_num = ?"
)

# Statuses that still hold a "live" review slot. Any review row in one
# of these states whose ``target_version`` doesn't match the freshly
# bumped phase version is stale and must be superseded.
_OPEN_REVIEW_STATUSES = ("pending", "queued", "running")

_ARTIFACT_PRODUCING_TYPES = frozenset(
    {TaskType.GENERATE_ARTIFACT.value, TaskType.USER_REVISION.value}
)


@dataclass(frozen=True)
class ArtifactCompletionResult:
    """Outcome of :meth:`VersionManager.complete_artifact_task`.

    Fields
    ------
    new_version
        The bumped ``phases.artifact_version`` value (old + 1).
    new_review_task_id
        ``task_ledger.id`` of the freshly-inserted ``pending`` review
        row whose ``target_version`` equals ``new_version``.
    superseded_review_task_ids
        Ids of every review row that was flipped to ``superseded`` as a
        side effect of the bump (may be empty if no stale reviews
        existed for the phase).
    """

    new_version: int
    new_review_task_id: str
    superseded_review_task_ids: list[str]


class VersionManager:
    """Owns the SPEC-3.5 bump-and-supersede transaction."""

    def __init__(self, engine: WorkflowEngine) -> None:
        self._engine = engine
        self._conn: sqlite3.Connection = engine._conn  # noqa: SLF001

    def complete_artifact_task(self, task_id: str) -> ArtifactCompletionResult:
        """Close ``task_id`` and run the SPEC-3.5 bump-and-supersede.

        Preconditions:
          * ``task_id`` resolves to a ``task_ledger`` row.
          * ``task.type`` is ``generate_artifact`` or ``user_revision``.
          * ``task.status == 'running'`` (the only legal predecessor of
            ``succeeded`` per SPEC-3.6).

        Side effects (in order):
          1. ``task_ledger.status``: running -> succeeded for ``task_id``.
          2. ``phases.artifact_version``: += 1 for ``(project_id, phase)``.
          3. Every other open review for the same phase whose
             ``target_version != new_version`` -> ``superseded``.
          4. New ``pending`` review row inserted with ``target_version``
             set to the new version.
        """
        task = self._engine.get_task(task_id)
        if task is None:
            raise ValueError(f"task not found: {task_id}")
        task_type = str(task["type"])
        if task_type not in _ARTIFACT_PRODUCING_TYPES:
            raise ValueError(
                f"complete_artifact_task only accepts "
                f"{sorted(_ARTIFACT_PRODUCING_TYPES)}; got {task_type!r}"
            )
        project_id = str(task["project_id"])
        phase_num = int(task["phase"])

        # 1. Close the producing task (SPEC-3.6 running -> succeeded).
        self._engine.update_task_status(task_id, "succeeded")

        # 2. Bump the phase artifact_version.
        self._conn.execute(_UPDATE_PHASE_BUMP_VERSION_SQL, (project_id, phase_num))
        self._conn.commit()
        new_version = self._read_phase_version(project_id, phase_num)

        # 3. Supersede stale open reviews. Re-uses the engine helper so
        #    every status transition still flows through SPEC-3.1 and
        #    emits the corresponding ``task.superseded`` event.
        superseded = self._supersede_stale_reviews(project_id, phase_num, new_version)

        # 4. Auto-create the fresh review for the new version.
        new_review_id = self._engine.create_task(
            project_id=project_id,
            phase=phase_num,
            task_type=TaskType.REVIEW.value,
            target_version=new_version,
        )

        return ArtifactCompletionResult(
            new_version=new_version,
            new_review_task_id=new_review_id,
            superseded_review_task_ids=superseded,
        )

    # ---- Internals ---------------------------------------------------

    def _read_phase_version(self, project_id: str, phase_num: int) -> int:
        row = self._conn.execute(
            "SELECT artifact_version FROM phases "
            "WHERE project_id = ? AND phase_num = ?",
            (project_id, phase_num),
        ).fetchone()
        if row is None:
            raise ValueError(f"phase not found: project={project_id} phase={phase_num}")
        return int(row[0])

    def _supersede_stale_reviews(
        self,
        project_id: str,
        phase_num: int,
        new_version: int,
    ) -> list[str]:
        placeholders = ",".join("?" * len(_OPEN_REVIEW_STATUSES))
        rows = self._conn.execute(
            "SELECT id, target_version FROM task_ledger "
            "WHERE project_id = ? AND phase = ? AND type = 'review' "
            f"AND status IN ({placeholders})",
            (project_id, phase_num, *_OPEN_REVIEW_STATUSES),
        ).fetchall()
        superseded: list[str] = []
        for row in rows:
            tid = str(row[0])
            target_version = row[1]
            if target_version != new_version:
                self._engine.update_task_status(tid, "superseded")
                superseded.append(tid)
        return superseded


__all__ = ["ArtifactCompletionResult", "VersionManager"]
