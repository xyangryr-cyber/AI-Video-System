// [SPEC-A-010] EventType -- the 17 WebSocket broadcast event types.
// Authority: docs/specs/SPEC-A-contracts.md SPEC-11A.
//
// Keep in lockstep with src/shared/constants/event_types.py. Streaming events
// (stream.token, stream.done) and the audit-only preference.rollback are
// defined in src/shared/types/events.ts; they MUST NOT appear here.

export const EVENT_TYPES = [
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
] as const;

export type EventType = (typeof EVENT_TYPES)[number];
