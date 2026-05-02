// ProjectState type (SPEC-0A.3). Mirror of src/shared/schemas/project_state.py.

import type { MasterAudioRef } from "./audio_master";

export type PhaseStatus =
  | "pending"
  | "active"
  | "completed"
  | "skipped"
  | "invalidated";

export type ArtifactStatus = "ok" | "damaged" | "missing";
export type ReviewStatus = "pending" | "passed" | "failed";
export type ProjectStatus = "active" | "completed" | "archived";

export interface ProjectInfo {
  project_id: string;
  title: string;
  description: string;
  current_phase: number;             // 0..11
  status: ProjectStatus;
  category: string;
  updated_at: string;                // ISO 8601 timestamp
}

export interface PhaseState {
  phase_num: number;
  phase_name: string;
  status: PhaseStatus;
  artifact_version: number;
  artifact_status: ArtifactStatus | null;
  // Built by API layer from phases.artifact_path:
  // `/api/projects/{id}/phases/{phase}/artifact`
  artifact_url: string | null;
  // Derived from task_ledger (see SPEC-0A.3):
  //   no review task -> null
  //   running/pending -> 'pending'
  //   succeeded PASS  -> 'passed'
  //   succeeded FAIL  -> 'failed'
  review_status: ReviewStatus | null;
  preferences_confirmed: boolean;
  style_lock_path: string | null;
}

export interface ActiveTask {
  task_id: string;
  type: string;
  status: string;
  progress: number;                  // 0..100
  agent_name: string | null;
}

export interface Preferences {
  pending_candidates: number;
  last_confirmed_at: string | null;
}

// Aggregated from system_status table rows with valid_until > NOW().
export interface SystemStatus {
  all_critical_ok: boolean;
  degraded_services: string[];
}

// SPEC-A-102 / SPEC-0A.3 v3.16: per-phase timeline entry for
// ProjectState.phase_history. Monotonic: reached_at is set when the
// phase is first entered; completed_at / last_revision_at are set
// opportunistically by the WorkflowEngine.
export interface PhaseHistoryEntry {
  phase: number;               // 0..11
  reached_at: string;          // ISO 8601
  completed_at?: string;
  last_revision_at?: string;
}

export interface ProjectState {
  project: ProjectInfo;
  phases: PhaseState[];
  active_tasks: ActiveTask[];
  preferences: Preferences;
  system_status: SystemStatus;
  // SPEC-A-013: hydrated from projects.master_audio_ref.
  // Null until Gate 4/5/6 flips the pointer.
  master_audio_ref?: MasterAudioRef | null;
  // SPEC-A-102 v3.16: high-water phase mark (>= current_phase). Backfilled
  // by the V004 migration to current_phase for legacy rows.
  latest_reached_phase: number;
  phase_history: PhaseHistoryEntry[];
}

export type { MasterAudioRef } from "./audio_master";
