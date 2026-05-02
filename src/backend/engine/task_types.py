"""[SPEC-C-002] Task data structures -- enums + validated Task model.

Authority: docs/specs/SPEC-C-backend-core.md SPEC-3.2 and
docs/specs/SPEC-A-contracts.md SPEC-1B (task_ledger DDL).

Defines:
  - ``TaskType``: the 14 canonical task types (no ``await_user``).
  - ``TaskStatus``: the 7 task_ledger status values.
  - ``Task``: Pydantic model enforcing per-type field constraints
    (AC-2: review has no ``produces_version``; ``generate_artifact``
    has no ``target_version``; review requires ``target_version``).
  - ``make_task_id``: ``t_<6-digit>`` formatter used by WorkflowEngine.
"""

from __future__ import annotations

import re
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


TASK_ID_PATTERN = re.compile(r"^t_\d{6}$")


class TaskType(str, Enum):
    """The 8 canonical task_ledger.type values (SPEC-3.2).

    ``await_user`` MUST NOT appear here; SPEC-3.2 retired it.
    """

    GENERATE_ARTIFACT = "generate_artifact"
    REGENERATE_SECTION = "regenerate_section"
    USER_REVISION = "user_revision"
    REVIEW = "review"
    RESEARCH = "research"
    VERIFY = "verify"
    CROSS_CHECK = "cross_check"
    USER_ANNOTATION = "user_annotation"
    GENERATE_NARRATION = "generate_narration"
    PREVIEW_MIX = "preview_mix"
    PLAN_LAYOUT = "plan_layout"
    RENDER_KEYFRAMES = "render_keyframes"
    COMPOSE_ROUGH_CUT = "compose_rough_cut"
    EXPORT_FINAL = "export_final"


class TaskStatus(str, Enum):
    """The 7 task_ledger.status values (SPEC-1B DDL)."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    SUPERSEDED = "superseded"
    TIMEOUT = "timeout"


_TYPES_WITH_PRODUCES_VERSION = frozenset(
    {
        TaskType.GENERATE_ARTIFACT,
        TaskType.USER_REVISION,
        TaskType.GENERATE_NARRATION,
        TaskType.PREVIEW_MIX,
        TaskType.PLAN_LAYOUT,
        TaskType.RENDER_KEYFRAMES,
        TaskType.COMPOSE_ROUGH_CUT,
        TaskType.EXPORT_FINAL,
    }
)
_TYPES_WITH_TARGET_VERSION = frozenset({TaskType.REVIEW})


class Task(BaseModel):
    """Validated in-memory Task model backing a task_ledger row.

    Enforces SPEC-3.2 per-type field constraints (AC-2):
      - ``review``: ``target_version`` required; ``produces_version`` forbidden.
      - ``generate_artifact`` / ``user_revision``: ``produces_version`` allowed;
        ``target_version`` forbidden.
      - other types: neither version field is allowed.
    """

    model_config = ConfigDict(extra="forbid", use_enum_values=False)

    id: str = Field(pattern=TASK_ID_PATTERN.pattern)
    project_id: str = Field(min_length=1)
    phase: int
    type: TaskType
    status: TaskStatus = TaskStatus.PENDING
    depends_on: Optional[list[str]] = None
    produces_version: Optional[int] = None
    target_version: Optional[int] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    result_ref: Optional[str] = None

    @model_validator(mode="after")
    def _enforce_version_fields(self) -> "Task":
        task_type = self.type
        if task_type in _TYPES_WITH_TARGET_VERSION:
            if self.produces_version is not None:
                raise ValueError(
                    f"task.type={task_type.value} must not carry "
                    "produces_version (SPEC-3.2 AC-2)"
                )
            if self.target_version is None:
                raise ValueError(
                    f"task.type={task_type.value} requires target_version "
                    "(SPEC-3.5 supersede rule)"
                )
        elif task_type in _TYPES_WITH_PRODUCES_VERSION:
            if self.target_version is not None:
                raise ValueError(
                    f"task.type={task_type.value} must not carry "
                    "target_version (SPEC-3.2 AC-2)"
                )
        else:
            if self.produces_version is not None:
                raise ValueError(
                    f"task.type={task_type.value} must not carry produces_version"
                )
            if self.target_version is not None:
                raise ValueError(
                    f"task.type={task_type.value} must not carry target_version"
                )
        return self


def make_task_id(seq: int) -> str:
    """Format a monotonic sequence number as ``t_<6-digit>`` (SPEC-3.2 AC-1).

    Raises ``ValueError`` for seq outside ``1..999999``.
    """
    if seq < 1 or seq > 999_999:
        raise ValueError(f"task id sequence must fit 6 digits (1..999999); got {seq}")
    return f"t_{seq:06d}"


__all__ = [
    "TASK_ID_PATTERN",
    "Task",
    "TaskStatus",
    "TaskType",
    "make_task_id",
]
