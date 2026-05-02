"""[SPEC-C-022] P8 starter — MaterialReadinessCheck wiring + shot-blocked broadcast.

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §C-AUDP7A-7.

Single entry point the WorkflowEngine calls to start the async P8
render phase. The function:

  1. Invokes :class:`~src.backend.services.material_readiness_check.MaterialReadinessCheck`
     against ``MaterialManifest`` + ``ShotMaterialBindings``.
  2. On ``ok=True``, returns ``P8StartResult(started=True, ...)`` so the
     caller can enqueue the P8 render task.
  3. On ``ok=False``, broadcasts a :class:`PhaseShotBlockedEvent` per
     blocked shot via the injected
     :class:`~src.backend.engine.event_publisher.ShotBlockedPublisher`
     and returns ``P8StartResult(started=False, ...)`` — P8 does **not**
     advance, and the FSM should set the ``phase_7a`` rollback flag.

The FSM-side rollback flag is set by the caller (WorkflowEngine); this
module only owns the Check + broadcast handshake so it stays trivially
unit-testable without a DB / Huey stack.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.backend.engine.event_publisher import ShotBlockedPublisher
from src.backend.services.material_readiness_check import (
    MaterialReadinessCheck,
    ReadinessResult,
)
from src.shared.schemas.material_manifest import MaterialManifest
from src.shared.schemas.shot_material_bindings import ShotMaterialBindings
from src.shared.schemas.ws_events import PhaseShotBlockedEvent


@dataclass
class P8StartResult:
    started: bool
    readiness: ReadinessResult
    emitted_events: list[PhaseShotBlockedEvent] = field(default_factory=list)


def start_p8(
    *,
    project_id: str,
    manifest: MaterialManifest,
    bindings: ShotMaterialBindings,
    publisher: ShotBlockedPublisher,
) -> P8StartResult:
    """Run the P8 pre-flight gate and broadcast blockers if it fails."""
    readiness = MaterialReadinessCheck.check(manifest=manifest, bindings=bindings)
    if readiness.ok:
        return P8StartResult(started=True, readiness=readiness)

    emitted: list[PhaseShotBlockedEvent] = []
    for blocked in readiness.blocked_shots:
        event = publisher.publish(
            project_id=project_id,
            shot_id=blocked.shot_id,
            error_code=blocked.error_code,
            blocking_material_ids=list(blocked.blocking_material_ids),
        )
        emitted.append(event)
    return P8StartResult(started=False, readiness=readiness, emitted_events=emitted)


__all__ = ["P8StartResult", "start_p8"]
