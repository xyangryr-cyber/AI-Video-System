// [SPEC-A-006] Frontend-facing response payload types for SPEC-1A REST endpoints.
// Authority: docs/specs/SPEC-A-contracts.md SPEC-1A.
// Error responses follow ErrorResponse in ./error_response.ts (SPEC-13A).

export interface OkResponse {
  ok: true;
}

export interface CreateProjectResponse {
  project_id: string;
}

export interface AdvanceResponse {
  phase: number;
  gate_result: Record<string, unknown>;
}

export interface SkipResponse {
  phase: number;
}

export interface RollbackResponse {
  phase: number;
  invalidated_phases: number[];
}

export interface ChatResponse {
  action: string;
  response: string;
  details?: Record<string, unknown>;
}

export interface PreferencesConfirmResponse {
  ok: true;
}

export interface PreferencesUpdateResponse {
  ok: true;
  snapshot_id: string;
}

export interface SnapshotRollbackResponse {
  ok: true;
  new_snapshot_id: string;
}

export interface CostsResponse {
  total_cost_usd: number;
  by_phase: Record<string, number>;
}

export interface EventsResponse {
  events: Array<Record<string, unknown>>;
}
