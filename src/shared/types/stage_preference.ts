// [SPEC-A-101] StagePreference cross-language contract.
// Mirror of src/shared/schemas/stage_preference.py.
// Authority: docs/specs/SPEC-A-contracts.md §A-BDD-2 (SPEC-0A.9).

export type StagePreferenceScope =
  | "global"
  | "cross_project"
  | "project"
  | "stage";

export type StagePreferenceStage =
  | "P2_script"
  | "P3_polish"
  | "P4_tts"
  | "P5_bgm"
  | "P6_sfx"
  | "P7_storyboard"
  | "P8_keyframe"
  | "P9_broll"
  | "P10_roughcut"
  | "P11_finalize";

export type StagePreferenceSource =
  | "user_explicit"
  | "extracted_from_revision"
  | "extracted_from_confirmation";

export interface StagePreference {
  preference_id: string;
  scope: StagePreferenceScope;
  stage?: StagePreferenceStage;
  key: string;
  value: string | number | boolean;
  source: StagePreferenceSource;
  applies_to_artifacts: string[];
  evidence_segment_id?: string;
  created_at: string;
  expires_at?: string;
}

// Per-phase glob-prefix patterns for preference-key injection
// (see src/shared/constants/stage_injection_matrix.py for the Python authority).
export const STAGE_INJECTION_MATRIX: Record<string, readonly string[]> = {
  P4_tts: ["tts.*"],
  P5_bgm: ["bgm.*"],
  P6_sfx: ["sfx.*"],
  P7_storyboard: ["storyboard.*", "visual.*"],
  P8_keyframe: ["chart.*", "visual.*"],
  P9_broll: ["broll.*"],
};
