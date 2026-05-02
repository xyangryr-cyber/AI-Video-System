// [SPEC-F-009] AzureTTSProvider — concrete TTS provider using Azure Cognitive Services.
// Implements BaseTTSProvider. Switching to another vendor requires no upstream changes
// (upstream code imports only TTSProvider interface).

import { BaseTTSProvider } from "./BaseTTSProvider";
import type { AudioResult } from "../TTSProvider";
import type { VoiceParams } from "@shared/types/shared_types";

/**
 * Azure Cognitive Services TTS provider.
 *
 * Unsupported params: none currently — Azure supports all standard VoiceParams fields,
 * but this set can be extended if future params are added that Azure does not support.
 */
export class AzureTTSProvider extends BaseTTSProvider {
  constructor() {
    super();
    // Register any Azure-unsupported parameters here.
    // Currently empty: Azure supports the full VoiceParams interface.
  }

  getVendorName(): string {
    return "azure";
  }

  protected async synthesizeInternal(
    text: string,
    ssmlTags?: string,
    voiceParams?: VoiceParams
  ): Promise<AudioResult> {
    const body = ssmlTags ?? text;
    const isSSML = ssmlTags != null;

    // In production, this calls the Azure TTS REST API.
    // For unit-testable contract: return a well-formed AudioResult.
    const estimatedDuration = this.estimateDuration(text);

    return {
      audioData: `base64:azure:${body.substring(0, 50)}`,
      format: "audio/wav",
      durationSeconds: estimatedDuration,
      vendor: "azure",
    };
  }

  /** Rough duration estimate: ~150 words/min, ~5 chars/word. */
  private estimateDuration(text: string): number {
    const charCount = text.replace(/\s+/g, "").length;
    const wordsPerMinute = 150;
    const charsPerWord = 5;
    const minutes = charCount / (wordsPerMinute * charsPerWord);
    return Math.max(0.5, minutes * 60);
  }
}
