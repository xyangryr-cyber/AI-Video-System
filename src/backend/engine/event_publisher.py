"""[SPEC-C-022] ShotBlockedPublisher — P8 `phase.shot_blocked` broadcast.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-6 /
§C-AUDP7A-7. The ``phase.shot_blocked`` event is intentionally NOT a
member of :class:`~src.shared.constants.event_types.EventType` (SPEC-A-018
leaves the 17-event invariant intact); the payload schema lives in
:mod:`src.shared.schemas.ws_events` and callers broadcast through this
thin publisher rather than the generic :class:`~src.backend.engine.event_bus.EventBus`.

The publisher is stateless and takes a ``Sink`` callable so the WS broker
/ DB writer / test double can all slot in without importing backend-
private state. Payload is constructed from
:class:`~src.shared.schemas.ws_events.PhaseShotBlockedEvent`, which
enforces the ``error_code ∈ {material_missing, material_unverified}``
and ``phase == "P8"`` invariants at validation time.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, Literal

from src.shared.schemas.ws_events import (
    PHASE_SHOT_BLOCKED_TYPE,
    PhaseShotBlockedEvent,
)

Sink = Callable[[str, str, dict[str, Any]], None]
"""``(project_id, event_type, payload_dict) -> None`` — side-effect sink.

The WorkflowEngine adapter forwards this to the ``events`` row writer +
WebSocket broker; tests inject a capture list.
"""


def _iso_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


class ShotBlockedPublisher:
    """Thin publisher for :class:`PhaseShotBlockedEvent`."""

    def __init__(self, *, sink: Sink) -> None:
        self._sink = sink

    def publish(
        self,
        *,
        project_id: str,
        shot_id: str,
        error_code: Literal["material_missing", "material_unverified"],
        blocking_material_ids: list[str],
    ) -> PhaseShotBlockedEvent:
        event = PhaseShotBlockedEvent(
            type=PHASE_SHOT_BLOCKED_TYPE,
            project_id=project_id,
            phase="P8",
            shot_id=shot_id,
            error_code=error_code,
            blocking_material_ids=blocking_material_ids,
            ts=_iso_now(),
        )
        self._sink(
            project_id,
            PHASE_SHOT_BLOCKED_TYPE,
            event.model_dump(),
        )
        return event


__all__ = ["ShotBlockedPublisher", "Sink"]
