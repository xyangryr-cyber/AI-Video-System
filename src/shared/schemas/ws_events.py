"""[SPEC-A-018] WebSocket event schemas added by SPEC-11A v3.17.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-6
(PRD-DELTA-08 / TECH-DELTA-07).

The 17 v3.15/v3.16 event payload schemas live in
``src.shared.schemas.events`` and are frozen; v3.17 additions live here to
preserve SPEC-A-010 invariants (``EventType`` enum stays at 17, envelope
stays unchanged) without editing the frozen surface.

Scope: ``PhaseShotBlockedEvent`` -- emitted from P8 when
:class:`~src.backend.services.material_readiness.MaterialReadinessCheck`
blocks rendering of a shot because the shot's bound material is either
missing from ``MaterialManifest`` or present-but-unverified.

The event's ``type`` string (``phase.shot_blocked``) is deliberately
**not** a member of :class:`~src.shared.constants.event_types.EventType`
so existing `TestAC11No18thEventType` and `TestAC1EventTypeEnumExactly17`
invariants continue to hold. Consumers that need it import
``PHASE_SHOT_BLOCKED_TYPE`` from this module.
"""

from __future__ import annotations

import re
from typing import List, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


_ISO8601_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d+)?"
    r"(?:Z|[+-]\d{2}:\d{2})$"
)


PHASE_SHOT_BLOCKED_TYPE: Literal["phase.shot_blocked"] = "phase.shot_blocked"
"""The `type` discriminator for :class:`PhaseShotBlockedEvent` broadcasts."""


class PhaseShotBlockedEvent(BaseModel):
    """P8 per-shot blocking event (SPEC-11A v3.17 addition).

    This is a flat message shape (envelope + payload in one model) because
    the v3.17 event is P8-specific and does not benefit from the generic
    ``WsEventEnvelope + payload-registry`` indirection used by the 17
    v3.15/v3.16 events. The ``type`` and ``phase`` fields are both locked
    to single Literal values so a mistyped broadcast fails pydantic
    validation rather than silently leaking.

    Fields:
        type: always "phase.shot_blocked".
        project_id: the project whose shot is blocked.
        phase: always "P8" (this event only fires in the rendering phase).
        shot_id: the specific shot that is blocked.
        error_code: which material-readiness failure triggered the block;
            one of "material_missing" | "material_unverified". Note that
            "render_failed" is deliberately **not** an allowed value -- a
            render exception is not a per-shot block, it surfaces via
            `task.failed` (SPEC-11A 17-event list).
        blocking_material_ids: the material_manifest IDs the shot depends
            on that failed the readiness check. Always non-empty when this
            event is emitted.
        ts: ISO8601 UTC timestamp.
    """

    model_config = ConfigDict(extra="forbid")

    type: Literal["phase.shot_blocked"]
    project_id: str
    phase: Literal["P8"]
    shot_id: str
    error_code: Literal["material_missing", "material_unverified"]
    blocking_material_ids: List[str] = Field(min_length=1)
    ts: str

    @field_validator("ts")
    @classmethod
    def _validate_iso8601(cls, value: str) -> str:
        if not isinstance(value, str) or not _ISO8601_RE.match(value):
            raise ValueError(f"ts must be ISO8601, got {value!r}")
        return value


__all__ = [
    "PHASE_SHOT_BLOCKED_TYPE",
    "PhaseShotBlockedEvent",
]
