// [SPEC-A-015] MaterialManifest types (TypeScript mirror).
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-3.
//
// Keep in lockstep with src/shared/schemas/material_manifest.py and
// schemas/material_manifest.schema.json.

export type MaterialType =
  | "chart"
  | "fact"
  | "news"
  | "figure"
  | "icon"
  | "image"
  | "video"
  | "quote";

export type RequiredLevel = "hard" | "soft";

export type SourceKind = "api" | "url" | "internal";

// Verification-status state machine:
//   pending -> verified | rejected | missing
//   {verified, rejected, missing} -> pending  ONLY via supplement flow
// See validate_verification_status_transition in material_manifest.py.
export type VerificationStatus =
  | "pending"
  | "verified"
  | "rejected"
  | "missing";

export interface MaterialSource {
  kind: SourceKind;
  ref: string;
}

export interface MaterialEntry {
  material_id: string; // ^mat_\d{3,}$
  shot_id: string; // ^shot_\d{2,}$
  material_type: MaterialType;
  required: RequiredLevel;
  source: MaterialSource;
  verification_status: VerificationStatus;
  fetched_at: string; // ISO-8601 date-time
  verified_at?: string; // ISO-8601 date-time
  rationale: string;
  evidence_ref?: string;
}

export interface MaterialManifest {
  project_id: string;
  phase: "7A";
  materials: MaterialEntry[];
}
