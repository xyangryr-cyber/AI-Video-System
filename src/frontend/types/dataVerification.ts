export type TrustLevel = "llm_generated" | "user_verified" | "stale";
export type VerificationStatus = "pending" | "verified" | "failed" | "stale";
export type FactCheckVerdict = "confirmed" | "refuted" | null;

export interface DataPoint {
  id: string;
  value: string;
  source: string;
  trust_level: TrustLevel;
  verification_status: VerificationStatus;
  verified_at: string | null;
  fact_checker_notes: string | null;
  verdict: FactCheckVerdict;
}
