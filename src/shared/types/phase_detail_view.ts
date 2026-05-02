// [SPEC-A-102] PhaseDetailView cross-language contract (SPEC-0A.10).
// Mirror of src/shared/schemas/phase_detail_view.py.
// Authority: docs/specs/SPEC-A-contracts.md §A-BDD-3.

export type PhaseDetailStatus =
  | "not_started"
  | "in_progress"
  | "completed"
  | "invalidated";

export interface PhaseDetailArtifact {
  path: string;
  version: number;
  size_bytes: number;
  updated_at: string;
}

export interface PhaseDetailReviewerResult {
  reviewer_name: string;
  verdict: "PASS" | "FAIL";
  ran_at: string;
  notes: string[];
}

export interface PhaseDetailGateResult {
  gate_name: string;
  verdict: "PASS" | "FAIL";
  checks: Array<{ name: string; passed: boolean }>;
}

export interface PhaseDetailClaimSnapshotEntry {
  claim_id: string;
  verification_status: string;
  blocking_level: string;
}

export interface PhaseDetailPreferenceSnapshotEntry {
  scope: string;
  stage?: string;
  key: string;
  value: unknown;
}

export interface PhaseDetailDiff {
  added: string[];
  removed: string[];
  modified: string[];
}

export interface PhaseDetailOperation {
  ts: string;
  action: string;
  actor: "user" | "system";
  ref?: string;
}

export interface PhaseDetailView {
  project_id: string;
  phase: number;                 // 0..11
  status: PhaseDetailStatus;
  artifacts: PhaseDetailArtifact[];
  reviewer_results: PhaseDetailReviewerResult[];
  gate_result?: PhaseDetailGateResult | null;
  claim_snapshot: PhaseDetailClaimSnapshotEntry[];
  preference_snapshot: PhaseDetailPreferenceSnapshotEntry[];
  diff_with_previous_version?: PhaseDetailDiff | null;
  operation_history: PhaseDetailOperation[];
  read_only: boolean;            // true iff phase != current_phase
  current_phase: number;         // 0..11
}
