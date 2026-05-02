// [SPEC-A-018] WebSocket event schemas added by SPEC-11A v3.17 (TypeScript).
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-6.
//
// The 17 v3.15/v3.16 event types + payload interfaces live in
// src/shared/types/events.ts (frozen). v3.17 additions live here to preserve
// the `EventType`-exactly-17 invariant (test_event_schemas.py::TestAC11)
// while extending the WS surface.
//
// Keep in lockstep with src/shared/schemas/ws_events.py.

export const PHASE_SHOT_BLOCKED_TYPE = "phase.shot_blocked" as const;
export type PhaseShotBlockedType = typeof PHASE_SHOT_BLOCKED_TYPE;

// The material-readiness failure classes that can trigger a shot block.
// "render_failed" is intentionally NOT in this union -- a render exception
// surfaces via `task.failed` (SPEC-11A 17-event set), not as a per-shot
// block.
export type PhaseShotBlockedErrorCode = "material_missing" | "material_unverified";

// The fully-flattened shape (envelope + payload in one object). v3.17
// events are P8-specific and skip the generic `WsEventEnvelope + payload`
// indirection used by the 17 v3.15/v3.16 events.
export interface PhaseShotBlockedEvent {
  type: PhaseShotBlockedType;
  project_id: string;
  phase: "P8";
  shot_id: string;
  error_code: PhaseShotBlockedErrorCode;
  // Non-empty: the material_manifest IDs whose readiness check failed.
  blocking_material_ids: string[];
  // ISO8601 UTC timestamp (e.g. "2026-04-20T10:00:00Z").
  ts: string;
}
