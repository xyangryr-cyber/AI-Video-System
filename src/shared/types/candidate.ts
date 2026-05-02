// Candidate type (SPEC-0A.2). Mirror of src/shared/schemas/candidate.py.

export type PreviewType = "audio" | "image" | "video" | "color_palette";

export interface Candidate {
  candidate_id: string;            // 'cand_' + UUID
  preview_url: string;             // preview asset URL (trimmed clip)
  preview_type: PreviewType;
  style_tags: string[];
  description: string;
  is_recommended: boolean;         // system recommendation flag
  adjustable_params: Record<string, unknown>;
  rationale: string;               // why this was recommended
  raw_bgm_url?: string;            // full-length BGM (P5 only)
}

// Container enforcing the SPEC-0A.2 cap of 3 candidates per phase.
export interface CandidateList {
  candidates: Candidate[];
}
