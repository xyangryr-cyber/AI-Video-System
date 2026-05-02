// [SPEC-A-017] GET /artifacts/master_audio endpoint types.
//
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md §A-AUDP7A-5.
//
// Mirrors src/shared/schemas/api_master_audio.py.

export type MasterAudioPhase = 4 | 5 | 6;

export type MasterAudioKind =
  | 'narration_master'
  | 'bgm_mix_master'
  | 'final_audio_master';

export interface GetMasterAudioRequest {
  phase: MasterAudioPhase;
}

export interface GetMasterAudioResponse {
  master_audio_url: string;
  download_url: string;
  based_on_phase: MasterAudioPhase;
  kind: MasterAudioKind;
  // sha256:<64 hex> checksum; pattern enforced on the Pydantic side.
  checksum: string;
  version: number;
}

// Error codes (SPEC-A-017 §AC-3):
//   - phase ∉ [4,5,6]  → 400 'invalid_phase'
//   - master not ready → 404 'master_not_ready'
export type MasterAudioErrorCode = 'invalid_phase' | 'master_not_ready';

export const MASTER_AUDIO_ERROR_HTTP_STATUS: {
  readonly [K in MasterAudioErrorCode]: number;
} = {
  invalid_phase: 400,
  master_not_ready: 404,
} as const;
