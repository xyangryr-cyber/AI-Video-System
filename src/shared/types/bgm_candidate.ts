// [SPEC-C-017] BgmCandidate -- P5 BGM candidate card (v3.17 dual-URL shape).
// Mirror of src/shared/schemas/bgm_candidate.py.

export interface BgmCandidate {
  candidate_id: string;         // 'cand_' + [A-Za-z0-9_-]+
  preview_url: string;          // phase_5/bgm_mix_preview_{candidate_id}.mp3
  preview_type: "audio";
  raw_bgm_url: string;          // phase_5/bgm_candidates/*.mp3
  style_tags: string[];
  description: string;
  is_recommended: boolean;
  adjustable_params: Record<string, unknown>;
  rationale: string;
}

/**
 * Legacy v3.15 shape -- single `bgm_url` field. The Python-side
 * `BgmCandidate` model_validator accepts this payload and promotes
 * `bgm_url` into both `preview_url` and `raw_bgm_url` with a
 * DeprecationWarning. TS-side consumers SHOULD migrate to `BgmCandidate`.
 */
export interface LegacyBgmCandidate {
  candidate_id: string;
  bgm_url: string;
  preview_type: "audio";
  style_tags: string[];
  description: string;
  is_recommended: boolean;
  adjustable_params: Record<string, unknown>;
  rationale: string;
}
