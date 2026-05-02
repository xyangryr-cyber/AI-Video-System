// [SPEC-A-006] Frontend-facing request payload types for SPEC-1A REST endpoints.
// Authority: docs/specs/SPEC-A-contracts.md SPEC-1A.

export interface CreateProjectRequest {
  title: string;
  // Must be at least 10 characters (validated server-side).
  description: string;
}

export interface AdvanceRequest {
  confirmed_preferences?: Array<Record<string, unknown>>;
}

export interface RollbackRequest {
  target_phase: number;
}

export interface ChatRequest {
  message: string;
}

export interface PreferenceDecision {
  id: string;
  action: string;
  text?: string;
}

export interface PreferencesConfirmRequest {
  decisions: PreferenceDecision[];
}
