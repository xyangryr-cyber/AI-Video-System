"""Tests for [SPEC-A-010] WebSocket Event Payload Schemas (17 Events).

Authority: docs/specs/SPEC-A-contracts.md SPEC-11A.

Covers AC-1 .. AC-11 per tasks/SPEC-A/A-010-websocket-event-schemas.md.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError


EXPECTED_EVENT_TYPES = [
    "phase.entered",
    "phase.exited",
    "phase.invalidated",
    "task.created",
    "task.queued",
    "task.started",
    "task.progress",
    "task.completed",
    "task.failed",
    "task.superseded",
    "artifact.produced",
    "artifact.damaged",
    "review.started",
    "review.completed",
    "gate.passed",
    "gate.failed",
    "preference.extracted",
]


class TestAC1EventTypeEnumExactly17:
    """AC-1: EventType enum has exactly 17 values matching spec."""

    def test_event_type_enum_exactly_17(self):
        from src.shared.constants.event_types import EventType

        values = [e.value for e in EventType]
        assert len(values) == 17, f"Expected 17 EventType values, got {len(values)}"
        assert values == EXPECTED_EVENT_TYPES, (
            f"EventType values do not match spec order.\n"
            f"Got:      {values}\nExpected: {EXPECTED_EVENT_TYPES}"
        )


class TestAC2WsMessageEnvelope:
    """AC-2: WS envelope schema: {type, timestamp, project_id, payload}."""

    def test_ws_message_envelope(self):
        from src.shared.constants.event_types import EventType
        from src.shared.schemas.events import WsEventEnvelope

        fields = set(WsEventEnvelope.model_fields.keys())
        assert fields == {"type", "timestamp", "project_id", "payload"}, (
            f"Envelope fields must be exactly "
            f"{{type, timestamp, project_id, payload}}, got {fields}"
        )

        env = WsEventEnvelope(
            type=EventType.PHASE_ENTERED,
            timestamp="2026-04-19T10:00:00Z",
            project_id="proj_test",
            payload={"phase_num": 1, "phase_name": "P1_intake"},
        )
        assert env.type == EventType.PHASE_ENTERED
        assert env.timestamp == "2026-04-19T10:00:00Z"
        assert env.project_id == "proj_test"

        with pytest.raises(ValidationError):
            WsEventEnvelope(
                type=EventType.PHASE_ENTERED,
                timestamp="not-a-timestamp",
                project_id="proj_test",
                payload={},
            )


class TestAC3All17PayloadsDefined:
    """AC-3: Each of 17 event types has a dedicated payload Pydantic model."""

    def test_all_17_payloads_defined(self):
        from src.shared.constants.event_types import EventType
        from src.shared.schemas.events import EVENT_PAYLOAD_REGISTRY

        assert set(EVENT_PAYLOAD_REGISTRY.keys()) == {e for e in EventType}, (
            "EVENT_PAYLOAD_REGISTRY must cover exactly the 17 EventType values"
        )
        for event, model in EVENT_PAYLOAD_REGISTRY.items():
            assert hasattr(model, "model_fields"), (
                f"{event.value} payload must be a Pydantic model, got {model!r}"
            )


class TestAC4PhaseInvalidatedHasReason:
    """AC-4: phase.invalidated payload includes reason field."""

    def test_phase_invalidated_has_reason(self):
        from src.shared.schemas.events import PhaseInvalidatedPayload

        fields = PhaseInvalidatedPayload.model_fields
        assert "reason" in fields, "phase.invalidated must have `reason`"
        assert "phase_num" in fields, "phase.invalidated must have `phase_num`"

        # reason is required
        with pytest.raises(ValidationError):
            PhaseInvalidatedPayload(phase_num=3)  # type: ignore[call-arg]


class TestAC5TaskProgressRange:
    """AC-5: task.progress payload includes progress 0-100 and optional message."""

    def test_task_progress_range(self):
        from src.shared.schemas.events import TaskProgressPayload

        TaskProgressPayload(task_id="t1", progress=0)
        TaskProgressPayload(task_id="t1", progress=100)
        TaskProgressPayload(task_id="t1", progress=50, message="halfway")

        with pytest.raises(ValidationError):
            TaskProgressPayload(task_id="t1", progress=-1)
        with pytest.raises(ValidationError):
            TaskProgressPayload(task_id="t1", progress=101)

        fields = TaskProgressPayload.model_fields
        assert fields["message"].is_required() is False, "message must be optional"


class TestAC6ReviewCompletedVerdictEnum:
    """AC-6: review.completed payload includes verdict (PASS|FAIL), notes[], blocking_issues[]."""

    def test_review_completed_verdict_enum(self):
        from src.shared.schemas.events import ReviewCompletedPayload, ReviewVerdict

        assert {v.value for v in ReviewVerdict} == {"PASS", "FAIL"}

        payload = ReviewCompletedPayload(
            phase_num=3,
            reviewer_name="StyleReviewer",
            verdict=ReviewVerdict.PASS,
            notes=["looks good"],
            blocking_issues=[],
        )
        assert payload.verdict == ReviewVerdict.PASS
        assert payload.notes == ["looks good"]
        assert payload.blocking_issues == []

        with pytest.raises(ValidationError):
            ReviewCompletedPayload(
                phase_num=3,
                reviewer_name="StyleReviewer",
                verdict="MAYBE",  # type: ignore[arg-type]
                notes=[],
                blocking_issues=[],
            )


class TestAC7GateFailedChecksStructure:
    """AC-7: gate.failed payload includes failed_checks: [{check_name, reason}]."""

    def test_gate_failed_checks_structure(self):
        from src.shared.schemas.events import GateFailedPayload, FailedCheck

        payload = GateFailedPayload(
            phase_num=3,
            failed_checks=[
                FailedCheck(check_name="review_passed", reason="verdict is FAIL"),
                FailedCheck(check_name="no_running_tasks", reason="t_0001 running"),
            ],
        )
        assert payload.failed_checks[0].check_name == "review_passed"
        assert payload.failed_checks[0].reason == "verdict is FAIL"

        with pytest.raises(ValidationError):
            FailedCheck(check_name="review_passed")  # type: ignore[call-arg]


class TestAC8ArtifactDamagedTypeEnum:
    """AC-8: artifact.damaged payload includes damage_type (truncated|corrupted|missing)."""

    def test_artifact_damaged_type_enum(self):
        from src.shared.schemas.events import ArtifactDamagedPayload, DamageType

        assert {d.value for d in DamageType} == {"truncated", "corrupted", "missing"}

        ArtifactDamagedPayload(
            phase_num=4,
            artifact_path="data/proj_x/p4/timeline.json",
            damage_type=DamageType.CORRUPTED,
        )

        with pytest.raises(ValidationError):
            ArtifactDamagedPayload(
                phase_num=4,
                artifact_path="x.json",
                damage_type="shredded",  # type: ignore[arg-type]
            )


class TestAC9StreamEventsSeparate:
    """AC-9: stream.token and stream.done defined as separate non-EventType schemas."""

    def test_stream_events_separate(self):
        from src.shared.constants.event_types import EventType
        from src.shared.schemas.events import StreamTokenPayload, StreamDonePayload

        event_values = {e.value for e in EventType}
        assert "stream.token" not in event_values
        assert "stream.done" not in event_values

        tok = StreamTokenPayload(task_id="t1", token="hello", seq=0)
        assert tok.token == "hello" and tok.seq == 0
        done = StreamDonePayload(task_id="t1", full_text="hello world")
        assert done.full_text == "hello world"


class TestAC10PreferenceRollbackAuditOnly:
    """AC-10: preference.rollback is audit-only (not in EventType, marked no-broadcast)."""

    def test_preference_rollback_audit_only(self):
        from src.shared.constants.event_types import EventType
        from src.shared.schemas.events import (
            PreferenceRollbackPayload,
            AUDIT_ONLY_EVENTS,
        )

        event_values = {e.value for e in EventType}
        assert "preference.rollback" not in event_values, (
            "preference.rollback MUST NOT appear in EventType (audit-only)"
        )
        assert "preference.rollback" in AUDIT_ONLY_EVENTS

        PreferenceRollbackPayload(
            snapshot_id="snap_1",
            target_snapshot_id="snap_0",
            new_snapshot_id="snap_2",
        )


class TestAC11No18thEventType:
    """AC-11: No 18th EventType value exists in enum."""

    def test_no_18th_event_type(self):
        from src.shared.constants.event_types import EventType

        count = len(list(EventType))
        assert count == 17, (
            f"EventType must have EXACTLY 17 members; found {count}. "
            "Streaming (stream.*) and audit-only (preference.rollback) events "
            "MUST live in separate schemas, not EventType."
        )
