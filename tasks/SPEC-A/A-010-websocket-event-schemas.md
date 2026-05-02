# [SPEC-A-010] WebSocket Event Payload Schemas (17 Events)

## Metadata
- **task_id**: SPEC-A-010
- **spec_ref**: SPEC-11A
- **depends_on**: [SPEC-A-002]
- **priority**: P0
- **estimated_complexity**: M

## Scope
Define the EventType enum (exactly 17 values), the unified WS message envelope `{type, timestamp, project_id, payload}`, and payload schemas for all 17 event types. Also define the 2 streaming events (stream.token, stream.done) and the audit-only event (preference.rollback) as separate non-broadcast types.

## Allowed Files
- `src/shared/types/events.ts`
- `src/shared/schemas/events.py`
- `src/shared/constants/event_types.py`
- `src/shared/constants/event_types.ts`
- `tests/unit/contracts/test_event_schemas.py`

## Forbidden Files
- `src/backend/api/**`
- `src/backend/ws/**`
- `src/frontend/**`

## Acceptance Criteria
- [ ] AC-1: EventType enum has exactly 17 values matching spec (phase.entered through preference.extracted)
- [ ] AC-2: WS message envelope schema: {type: EventType, timestamp: ISO8601, project_id: string, payload: object}
- [ ] AC-3: Each of 17 event types has a dedicated payload Pydantic model with correct fields
- [ ] AC-4: phase.invalidated payload includes reason field
- [ ] AC-5: task.progress payload includes progress 0-100 and optional message
- [ ] AC-6: review.completed payload includes verdict enum (PASS|FAIL), notes[], blocking_issues[]
- [ ] AC-7: gate.failed payload includes failed_checks array of {check_name, reason}
- [ ] AC-8: artifact.damaged payload includes damage_type enum (truncated|corrupted|missing)
- [ ] AC-9: stream.token and stream.done defined as separate non-EventType schemas
- [ ] AC-10: preference.rollback defined as audit-only (not in EventType enum, marked no-broadcast)
- [ ] AC-11: No 18th EventType value exists in enum

## Verification Commands
```bash
pytest tests/unit/contracts/test_spec_a_010.py -v
mypy src/shared/schemas/events.py --strict
npx tsc --noEmit src/shared/types/events.ts
```

## Completion Definition
EventType enum has exactly 17 members. All 17 payload schemas defined and validated. Envelope schema enforced. Streaming and audit events defined separately. Tests cover each event type's payload, envelope structure, and enum completeness.

## Test Mapping
| AC | Test File | Test Function |
|---|---|---|
| AC-1 | tests/unit/contracts/test_spec_a_010.py | test_event_type_enum_exactly_17 |
| AC-2 | tests/unit/contracts/test_spec_a_010.py | test_ws_message_envelope |
| AC-3 | tests/unit/contracts/test_spec_a_010.py | test_all_17_payloads_defined |
| AC-4 | tests/unit/contracts/test_spec_a_010.py | test_phase_invalidated_has_reason |
| AC-5 | tests/unit/contracts/test_spec_a_010.py | test_task_progress_range |
| AC-6 | tests/unit/contracts/test_spec_a_010.py | test_review_completed_verdict_enum |
| AC-7 | tests/unit/contracts/test_spec_a_010.py | test_gate_failed_checks_structure |
| AC-8 | tests/unit/contracts/test_spec_a_010.py | test_artifact_damaged_type_enum |
| AC-9 | tests/unit/contracts/test_spec_a_010.py | test_stream_events_separate |
| AC-10 | tests/unit/contracts/test_spec_a_010.py | test_preference_rollback_audit_only |
| AC-11 | tests/unit/contracts/test_spec_a_010.py | test_no_18th_event_type |
