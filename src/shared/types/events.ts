// [SPEC-A-010] WebSocket event envelope and payload types (17 events).
// Authority: docs/specs/SPEC-A-contracts.md SPEC-11A.
//
// Keep in lockstep with src/shared/schemas/events.py. Streaming events
// (stream.token, stream.done) and the audit-only preference.rollback are
// defined below but are NOT part of EventType (see src/shared/constants/event_types.ts).

import type { EventType } from "../constants/event_types";

// ---- Enums used inside payloads -----------------------------------------

export type ReviewVerdict = "PASS" | "FAIL";
export type ReviewLevel = "L1" | "L2";
export type DamageType = "truncated" | "corrupted" | "missing";

// ---- The 17 payload interfaces (order = SPEC-11A table) -----------------

export interface PhaseEnteredPayload {
  phase_num: number;
  phase_name: string;
}

export interface PhaseExitedPayload {
  phase_num: number;
}

export interface PhaseInvalidatedPayload {
  phase_num: number;
  reason: string;
}

export interface TaskCreatedPayload {
  task_id: string;
  task_type: string;
  phase: number;
}

export interface TaskQueuedPayload {
  task_id: string;
}

export interface TaskStartedPayload {
  task_id: string;
  agent_name: string;
}

export interface TaskProgressPayload {
  task_id: string;
  // Range: 0..100 (inclusive) -- validated server-side.
  progress: number;
  message?: string;
}

export interface TaskCompletedPayload {
  task_id: string;
  result_ref?: string;
}

export interface TaskFailedPayload {
  task_id: string;
  error_code: string;
  error_message: string;
}

export interface TaskSupersededPayload {
  task_id: string;
  superseded_by?: string;
}

export interface ArtifactProducedPayload {
  phase_num: number;
  version: number;
  artifact_path: string;
}

export interface ArtifactDamagedPayload {
  phase_num: number;
  artifact_path: string;
  damage_type: DamageType;
}

export interface ReviewStartedPayload {
  phase_num: number;
  reviewer_name: string;
  level: ReviewLevel;
}

export interface FailedCheck {
  check_name: string;
  reason: string;
}

export interface ReviewCompletedPayload {
  phase_num: number;
  reviewer_name: string;
  verdict: ReviewVerdict;
  notes: string[];
  blocking_issues: string[];
}

export interface GatePassedPayload {
  phase_num: number;
}

export interface GateFailedPayload {
  phase_num: number;
  failed_checks: FailedCheck[];
}

export interface PreferenceCandidate {
  id: string;
  rule: string;
  // Range: 0..1 (inclusive) -- validated server-side.
  confidence: number;
}

export interface PreferenceExtractedPayload {
  candidates_count: number;
  candidates: PreferenceCandidate[];
}

// ---- Streaming payloads (NOT in EventType) ------------------------------

export interface StreamTokenPayload {
  task_id: string;
  token: string;
  seq: number;
}

export interface StreamDonePayload {
  task_id: string;
  full_text: string;
}

// ---- Audit-only payload (NOT in EventType, never broadcast) -------------

export interface PreferenceRollbackPayload {
  snapshot_id: string;
  target_snapshot_id: string;
  new_snapshot_id: string;
}

// ---- Envelope + discriminated union -------------------------------------

export interface WsEventEnvelope<P = unknown> {
  type: EventType;
  // ISO8601 UTC timestamp, e.g. "2026-04-19T10:00:00Z".
  timestamp: string;
  project_id: string;
  payload: P;
}

export type EventPayloadByType = {
  "phase.entered": PhaseEnteredPayload;
  "phase.exited": PhaseExitedPayload;
  "phase.invalidated": PhaseInvalidatedPayload;
  "task.created": TaskCreatedPayload;
  "task.queued": TaskQueuedPayload;
  "task.started": TaskStartedPayload;
  "task.progress": TaskProgressPayload;
  "task.completed": TaskCompletedPayload;
  "task.failed": TaskFailedPayload;
  "task.superseded": TaskSupersededPayload;
  "artifact.produced": ArtifactProducedPayload;
  "artifact.damaged": ArtifactDamagedPayload;
  "review.started": ReviewStartedPayload;
  "review.completed": ReviewCompletedPayload;
  "gate.passed": GatePassedPayload;
  "gate.failed": GateFailedPayload;
  "preference.extracted": PreferenceExtractedPayload;
};

export type WsEvent = {
  [K in EventType]: WsEventEnvelope<EventPayloadByType[K]> & { type: K };
}[EventType];

// Audit-only (never broadcast; written to events table only).
export const AUDIT_ONLY_EVENTS = ["preference.rollback"] as const;
export type AuditOnlyEventType = (typeof AUDIT_ONLY_EVENTS)[number];
