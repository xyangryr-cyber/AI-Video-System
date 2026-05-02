// [SPEC-F-009] TTSProvider interface — vendor abstraction for TTS synthesis.
// Upstream code imports only this interface; switching vendor requires no changes.

import type { VoiceParams } from "@shared/types/shared_types";

export interface AudioResult {
  /** Base64-encoded audio data */
  audioData: string;
  /** Audio format (e.g. "audio/wav", "audio/mpeg") */
  format: string;
  /** Duration in seconds */
  durationSeconds: number;
  /** The TTS vendor that produced this audio */
  vendor: string;
}

export interface TTSProvider {
  /**
   * Synthesize speech from text with SSML tags and voice parameters.
   *
   * @param text — plain text content to synthesize
   * @param ssmlTags — optional SSML markup string for prosody/emphasis
   * @param voiceParams — voice configuration (style, rate, volume, pitch)
   * @returns AudioResult with audio data and metadata
   */
  synthesize(text: string, ssmlTags?: string, voiceParams?: VoiceParams): Promise<AudioResult>;
}
