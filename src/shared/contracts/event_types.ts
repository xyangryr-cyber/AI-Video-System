// [SPEC-11A] WebSocket event types — TypeScript mirror of
// src/shared/contracts/event_types.py.
// Authority: docs/specs/SPEC-A-contracts.md SPEC-11A
// "WebSocket Event Envelope & Event Types".
// 17 event type strings in dot notation.

export const EVENT_TYPES = {
  PHASE_ENTERED: "phase.entered",
  PHASE_EXITED: "phase.exited",
  PHASE_INVALIDATED: "phase.invalidated",
  TASK_CREATED: "task.created",
  TASK_QUEUED: "task.queued",
  TASK_STARTED: "task.started",
  TASK_PROGRESS: "task.progress",
  TASK_COMPLETED: "task.completed",
  TASK_FAILED: "task.failed",
  TASK_SUPERSEDED: "task.superseded",
  ARTIFACT_PRODUCED: "artifact.produced",
  ARTIFACT_DAMAGED: "artifact.damaged",
  REVIEW_STARTED: "review.started",
  REVIEW_COMPLETED: "review.completed",
  GATE_PASSED: "gate.passed",
  GATE_FAILED: "gate.failed",
  PREFERENCE_EXTRACTED: "preference.extracted",
} as const;

export type EventType = (typeof EVENT_TYPES)[keyof typeof EVENT_TYPES];
