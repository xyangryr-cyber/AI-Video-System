// [SPEC-E-015] MasterAudioView — frontend View type mirroring MasterAudioArtifact.
// Keep in lockstep with src/shared/types/audio_master.ts and SPEC-A-013.
export type MasterAudioKind = "narration_master" | "bgm_mix_master" | "final_audio_master";

export type UpstreamMasterKind = "narration_master" | "bgm_mix_master";

export interface SourceRef {
  kind: UpstreamMasterKind;
  checksum: string;
}

interface MasterAudioCommon {
  file_path: string;
  based_on_phase: 4 | 5 | 6;
  derived_from_segments: string[];
  total_duration_seconds: number;
  checksum: string;
  version: number;
}

export interface NarrationMasterView extends MasterAudioCommon {
  kind: "narration_master";
}

export interface BgmMixMasterView extends MasterAudioCommon {
  kind: "bgm_mix_master";
  source_ref: SourceRef;
}

export interface FinalAudioMasterView extends MasterAudioCommon {
  kind: "final_audio_master";
  source_ref: SourceRef;
}

export type MasterAudioView = NarrationMasterView | BgmMixMasterView | FinalAudioMasterView;
