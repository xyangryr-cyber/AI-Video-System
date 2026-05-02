// [SPEC-A-013] MasterAudioArtifact types (TypeScript mirror).
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-1.
//
// Keep in lockstep with src/shared/schemas/audio_master.py and
// schemas/audio_master.schema.json.

export type MasterAudioKind =
  | "narration_master"
  | "bgm_mix_master"
  | "final_audio_master";

export type UpstreamMasterKind = "narration_master" | "bgm_mix_master";

export interface SourceRef {
  kind: UpstreamMasterKind;
  // sha256:<64-hex> format, e.g. "sha256:ab...".
  checksum: string;
}

interface MasterAudioCommon {
  file_path: string; // ^phase_[456a]/.+\.(mp3|wav)$
  based_on_phase: 4 | 5 | 6;
  // each entry matches ^seg_\d{2,}$
  derived_from_segments: string[];
  total_duration_seconds: number;
  checksum: string; // ^sha256:[a-f0-9]{64}$
  version: number; // >= 1
}

export interface NarrationMasterArtifact extends MasterAudioCommon {
  kind: "narration_master";
}

export interface BgmMixMasterArtifact extends MasterAudioCommon {
  kind: "bgm_mix_master";
  source_ref: SourceRef;
}

export interface FinalAudioMasterArtifact extends MasterAudioCommon {
  kind: "final_audio_master";
  source_ref: SourceRef;
}

// Discriminated union over `kind` -- mirrors the Pydantic annotated union.
export type MasterAudioArtifact =
  | NarrationMasterArtifact
  | BgmMixMasterArtifact
  | FinalAudioMasterArtifact;

// Compact shape stored on ProjectState.master_audio_ref (SPEC-0A.3).
export interface MasterAudioRef {
  kind: MasterAudioKind;
  file_path: string;
  based_on_phase: 4 | 5 | 6;
  checksum: string;
  version: number;
}
