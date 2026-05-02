"""[SPEC-C-022] Integration test — P8 starter blocks on unverified material.

AC-4: with `phase_7a` holding at least one HARD-required material that is
still PENDING, invoking ``start_p8`` must return ``started=False`` and
broadcast a ``phase.shot_blocked`` event with the blocked shot_id,
error_code, and blocking_material_ids.
"""

from __future__ import annotations

from typing import Any, List, Tuple

from src.backend.engine.event_publisher import ShotBlockedPublisher
from src.backend.engine.p8_starter import start_p8
from src.shared.schemas.material_manifest import (
    MaterialEntry,
    MaterialManifest,
    MaterialSource,
    MaterialType,
    RequiredLevel,
    SourceKind,
    VerificationStatus,
)
from src.shared.schemas.shot_material_bindings import (
    ShotBinding,
    ShotMaterialBindings,
)
from src.shared.schemas.ws_events import (
    PHASE_SHOT_BLOCKED_TYPE,
    PhaseShotBlockedEvent,
)


def _entry(
    material_id: str,
    shot_id: str,
    status: VerificationStatus = VerificationStatus.VERIFIED,
) -> MaterialEntry:
    return MaterialEntry(
        material_id=material_id,
        shot_id=shot_id,
        material_type=MaterialType.FACT,
        required=RequiredLevel.HARD,
        source=MaterialSource(kind=SourceKind.API, ref="ref"),
        verification_status=status,
        fetched_at="2026-04-24T00:00:00Z",
        rationale="test",
    )


def test_p8_blocked_event_emitted_with_payload() -> None:
    captured: List[Tuple[str, str, dict[str, Any]]] = []

    def sink(project_id: str, event_type: str, payload: dict[str, Any]) -> None:
        captured.append((project_id, event_type, payload))

    publisher = ShotBlockedPublisher(sink=sink)

    manifest = MaterialManifest(
        project_id="proj_c022",
        phase="7A",
        materials=[
            _entry(
                "mat_700",
                "shot_01",
                status=VerificationStatus.PENDING,
            ),
            _entry("mat_701", "shot_02"),
        ],
    )
    bindings = ShotMaterialBindings(
        bindings=[
            ShotBinding(
                shot_id="shot_01",
                required_materials=["mat_700"],
                optional_materials=[],
            ),
            ShotBinding(
                shot_id="shot_02",
                required_materials=["mat_701"],
                optional_materials=[],
            ),
        ]
    )

    result = start_p8(
        project_id="proj_c022",
        manifest=manifest,
        bindings=bindings,
        publisher=publisher,
    )

    assert result.started is False
    # Exactly one shot is blocked.
    assert len(result.emitted_events) == 1
    evt = result.emitted_events[0]
    assert isinstance(evt, PhaseShotBlockedEvent)
    assert evt.type == PHASE_SHOT_BLOCKED_TYPE == "phase.shot_blocked"
    assert evt.project_id == "proj_c022"
    assert evt.phase == "P8"
    assert evt.shot_id == "shot_01"
    assert evt.error_code == "material_unverified"
    assert evt.blocking_material_ids == ["mat_700"]

    # Sink received the broadcast with project_id + type + payload.
    assert len(captured) == 1
    project_id, event_type, payload = captured[0]
    assert project_id == "proj_c022"
    assert event_type == "phase.shot_blocked"
    assert payload["shot_id"] == "shot_01"
    assert payload["error_code"] == "material_unverified"
    assert payload["blocking_material_ids"] == ["mat_700"]


def test_p8_starts_when_all_verified() -> None:
    captured: List[Tuple[str, str, dict[str, Any]]] = []

    def sink(project_id: str, event_type: str, payload: dict[str, Any]) -> None:
        captured.append((project_id, event_type, payload))

    publisher = ShotBlockedPublisher(sink=sink)

    manifest = MaterialManifest(
        project_id="proj_c022",
        phase="7A",
        materials=[_entry("mat_710", "shot_01")],
    )
    bindings = ShotMaterialBindings(
        bindings=[
            ShotBinding(
                shot_id="shot_01",
                required_materials=["mat_710"],
                optional_materials=[],
            )
        ]
    )

    result = start_p8(
        project_id="proj_c022",
        manifest=manifest,
        bindings=bindings,
        publisher=publisher,
    )

    assert result.started is True
    assert result.emitted_events == []
    assert captured == []
