"""Tests for [SPEC-A-018] SPEC-11A v3.17 addition: `phase.shot_blocked`
WebSocket event (PhaseShotBlockedEvent schema).

Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-6
delta: PRD-DELTA-08 / TECH-DELTA-07

Covers AC-2 and AC-5 of tasks/SPEC-A/A-018-error-codes-and-shot-blocked-event.md.
AC-1, AC-3, AC-4 (error-code / log-event contract) live in
tests/unit/contracts/test_error_codes_v317.py.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError


class TestAC2:
    """AC-2: `PhaseShotBlockedEvent` Pydantic + TS 字段：type=`phase.shot_blocked` /
    project_id / phase=`P8` / shot_id / error_code ∈ {material_missing,
    material_unverified} / blocking_material_ids / ts ISO8601"""

    def test_event_payload_schema(self):
        """PhaseShotBlockedEvent has exactly the 7 documented fields and accepts a valid instance."""
        from src.shared.schemas.ws_events import PhaseShotBlockedEvent

        fields = set(PhaseShotBlockedEvent.model_fields.keys())
        assert fields == {
            "type",
            "project_id",
            "phase",
            "shot_id",
            "error_code",
            "blocking_material_ids",
            "ts",
        }, (
            f"PhaseShotBlockedEvent fields must be exactly "
            f"{{type, project_id, phase, shot_id, error_code, "
            f"blocking_material_ids, ts}}, got {fields}"
        )

        ev = PhaseShotBlockedEvent(
            type="phase.shot_blocked",
            project_id="proj_abc",
            phase="P8",
            shot_id="shot_007",
            error_code="material_missing",
            blocking_material_ids=["mat_001", "mat_002"],
            ts="2026-04-20T10:00:00Z",
        )
        assert ev.type == "phase.shot_blocked"
        assert ev.phase == "P8"
        assert ev.error_code == "material_missing"
        assert ev.blocking_material_ids == ["mat_001", "mat_002"]

        # `type` is locked to "phase.shot_blocked" (Literal).
        with pytest.raises(ValidationError):
            PhaseShotBlockedEvent(
                type="phase.shot_unblocked",  # type: ignore[arg-type]
                project_id="proj_abc",
                phase="P8",
                shot_id="shot_007",
                error_code="material_missing",
                blocking_material_ids=["mat_001"],
                ts="2026-04-20T10:00:00Z",
            )

        # `phase` is locked to "P8" (this event is P8-specific).
        with pytest.raises(ValidationError):
            PhaseShotBlockedEvent(
                type="phase.shot_blocked",
                project_id="proj_abc",
                phase="P7",  # type: ignore[arg-type]
                shot_id="shot_007",
                error_code="material_missing",
                blocking_material_ids=["mat_001"],
                ts="2026-04-20T10:00:00Z",
            )

        # `ts` must be ISO8601.
        with pytest.raises(ValidationError):
            PhaseShotBlockedEvent(
                type="phase.shot_blocked",
                project_id="proj_abc",
                phase="P8",
                shot_id="shot_007",
                error_code="material_missing",
                blocking_material_ids=["mat_001"],
                ts="not-a-timestamp",
            )

    def test_error_code_constrained_to_two_values(self):
        """PhaseShotBlockedEvent.error_code only accepts material_missing | material_unverified.

        render_failed describes a different failure class (rendering exception)
        and MUST NOT be emittable through a shot-blocked event.
        """
        from src.shared.schemas.ws_events import PhaseShotBlockedEvent

        for valid in ("material_missing", "material_unverified"):
            ev = PhaseShotBlockedEvent(
                type="phase.shot_blocked",
                project_id="proj_abc",
                phase="P8",
                shot_id="shot_007",
                error_code=valid,  # type: ignore[arg-type]
                blocking_material_ids=["mat_001"],
                ts="2026-04-20T10:00:00Z",
            )
            assert ev.error_code == valid

        # render_failed belongs to the render-failure class, not shot-blocked.
        with pytest.raises(ValidationError):
            PhaseShotBlockedEvent(
                type="phase.shot_blocked",
                project_id="proj_abc",
                phase="P8",
                shot_id="shot_007",
                error_code="render_failed",  # type: ignore[arg-type]
                blocking_material_ids=["mat_001"],
                ts="2026-04-20T10:00:00Z",
            )

        with pytest.raises(ValidationError):
            PhaseShotBlockedEvent(
                type="phase.shot_blocked",
                project_id="proj_abc",
                phase="P8",
                shot_id="shot_007",
                error_code="something_else",  # type: ignore[arg-type]
                blocking_material_ids=["mat_001"],
                ts="2026-04-20T10:00:00Z",
            )


class TestAC5:
    """AC-5: `PhaseShotBlockedEvent` 与 v3.16 既有 17 种事件不冲突（type 命名空间唯一）"""

    def test_event_type_namespace_unique(self):
        """`phase.shot_blocked` does not collide with any of the 17 v3.16 EventType values."""
        from src.shared.constants.event_types import EventType
        from src.shared.schemas.ws_events import PHASE_SHOT_BLOCKED_TYPE

        v316_event_values = {e.value for e in EventType}
        assert PHASE_SHOT_BLOCKED_TYPE == "phase.shot_blocked"
        assert PHASE_SHOT_BLOCKED_TYPE not in v316_event_values, (
            f"phase.shot_blocked collides with v3.16 EventType; type "
            f"namespace must be unique. v3.16 set: {v316_event_values}"
        )
        # v3.16 event set is frozen at 17 -- this task MUST NOT add to it.
        assert len(v316_event_values) == 17, (
            f"v3.16 EventType enum must remain at 17 values "
            f"(phase.shot_blocked lives in ws_events, not event_types). "
            f"Got {len(v316_event_values)}."
        )
