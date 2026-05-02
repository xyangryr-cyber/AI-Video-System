// [SPEC-A-100] Claim / VerificationRecord unified data model.
// Mirror of src/shared/schemas/claim.py. Authority: SPEC-A §A-BDD-1.
//
// `claim_id` accepts canonical "claim_{phase}_{seq}" and legacy v3.15
// "dp_*" (key_data_point.data_point_id) values.

export type ClaimType =
  | "fact"
  | "data"
  | "event"
  | "citation"
  | "image_backed";

export type SourcePhase = "P2" | "P7" | "P8" | "P9" | "user_input";

export type BlockingLevel = "hard" | "soft" | "none";

export type VerificationStatus =
  | "pending"
  | "verifying"
  | "verified"
  | "failed"
  | "stale"
  | "superseded"
  | "user_disputed";

export type VerifierType =
  | "fact_check_agent"
  | "financial_data_service"
  | "web_search"
  | "user_override";

export type Verdict = "verified" | "failed" | "inconclusive";

export interface TimeRange {
  start: string;
  end: string;
}

export interface SourceSpan {
  start_char: number;
  end_char: number;
  segment_id?: string;
}

export interface EvidenceRef {
  url?: string;
  doc_path?: string;
  snippet?: string;
}

export interface Claim {
  claim_id: string;
  claim_type: ClaimType;
  text: string;
  value?: number | string;
  unit?: string;
  entity?: string;
  time_range?: TimeRange;
  source_phase: SourcePhase;
  source_artifact: string;
  source_span?: SourceSpan;
  blocking_level: BlockingLevel;
  verification_status: VerificationStatus;
  created_at: string;
  updated_at: string;
}

export interface VerificationRecord {
  verification_id: string;
  claim_id: string;
  verifier_type: VerifierType;
  evidence_refs: EvidenceRef[];
  checked_at: string;
  expires_at?: string;
  verdict: Verdict;
  reason?: string;
  confidence?: number;
}
