// [SPEC-F-009] BaseTTSProvider — abstract base for TTS vendor implementations.
// Handles capability_gap logging for unsupported parameters.
// Concrete providers extend this class.

import type { TTSProvider, AudioResult } from "../TTSProvider";
import type { VoiceParams } from "@shared/types/shared_types";

export interface CapabilityGap {
  /** The parameter that is not supported */
  parameter: string;
  /** Human-readable reason */
  reason: string;
}

/**
 * BaseTTSProvider provides shared logic for capability-gap handling.
 * Concrete TTS vendors implement synthesizeInternal().
 */
export abstract class BaseTTSProvider implements TTSProvider {
  protected unsupportedParams: Set<string> = new Set();

  /**
   * Public synthesize entrypoint.
   * Checks for unsupported params -> logs capability_gap -> degrades gracefully.
   */
  async synthesize(
    text: string,
    ssmlTags?: string,
    voiceParams?: VoiceParams,
  ): Promise<AudioResult> {
    const gaps: CapabilityGap[] = [];

    if (voiceParams) {
      for (const param of this.unsupportedParams) {
        if (param in voiceParams) {
          gaps.push({
            parameter: param,
            reason: `vendor ${this.getVendorName()} does not support ${param}`,
          });
        }
      }
    }

    // Log capability_gap for each unsupported param — synthesis continues
    for (const gap of gaps) {
      console.warn(
        JSON.stringify({
          event: "capability_gap",
          vendor: this.getVendorName(),
          parameter: gap.parameter,
          reason: gap.reason,
        }),
      );
    }

    // Degrade gracefully: pass voiceParams through, vendor ignores unsupported fields
    try {
      return await this.synthesizeInternal(text, ssmlTags, voiceParams);
    } catch (err) {
      // Graceful degradation: wrap error, don't throw
      console.error(
        JSON.stringify({
          event: "capability_gap",
          vendor: this.getVendorName(),
          error: String(err),
          fallback: "returning empty audio result",
        }),
      );
      return this.emptyAudioResult();
    }
  }

  /** Subclasses implement vendor-specific synthesis. */
  protected abstract synthesizeInternal(
    text: string,
    ssmlTags?: string,
    voiceParams?: VoiceParams,
  ): Promise<AudioResult>;

  /** Return vendor name for logging. */
  abstract getVendorName(): string;

  /** Empty fallback result for degraded synthesis. */
  protected emptyAudioResult(): AudioResult {
    return {
      audioData: "",
      format: "audio/wav",
      durationSeconds: 0,
      vendor: this.getVendorName(),
    };
  }
}
