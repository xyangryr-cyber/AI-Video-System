export type ClaimType = "financial_data" | "fact" | "image_backed" | "citation";
export type ClaimVerificationStatus = "verified" | "unverified" | "user_disputed" | "superseded";
export type TrustLevel = "llm_generated" | "user_verified";
export type ViewMode = "table" | "card";

export interface ClaimRow {
  claim_id: string;
  claim_type: ClaimType;
  entity: string;
  value: string;
  verification_status: ClaimVerificationStatus;
  hard_blocking: boolean;
  source_phase: number;
  trust_level: TrustLevel;
}

export type FilterDimension = "claim_type" | "verification_status" | "source_phase" | "trust_level";

export interface ClaimFilters {
  claim_type?: ClaimType;
  verification_status?: ClaimVerificationStatus;
  source_phase?: number;
  trust_level?: TrustLevel;
}
