// [SPEC-A-014] SfxMixSegments types (TypeScript mirror).
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-2.
//
// Keep in lockstep with src/shared/schemas/sfx_mix_segments.py and
// schemas/sfx_mix_segments.schema.json.

// base_master must reference an upstream master
// (narration_master.mp3 from P4 or bgm_mix_master.mp3 from P5).
export type SfxBaseMaster =
  | "phase_4/narration_master.mp3"
  | "phase_5/bgm_mix_master.mp3";

export interface SfxMixSegment {
  segment_id: string; // ^seg_\d{2,}$
  // ^phase_6/sfx_applied_segments/seg_\d{2,}\.mp3$
  file_path: string;
  applied_triggers: string[]; // each matches ^trg_\d{3,}$
  checksum: string; // ^sha256:[a-f0-9]{64}$
  version: number; // >= 1
}

export interface SfxMixSegments {
  base_master: SfxBaseMaster;
  segments: SfxMixSegment[];
}
