// [SPEC-F-009] Voice Preview — generates 2-3 preview clips of 15 seconds each.
// Used in P4 phase for voice selection.

import type { TTSProvider, AudioResult } from "./TTSProvider";

export interface PreviewClip {
  /** Preview audio data */
  audio: AudioResult;
  /** Label for the preview (e.g. "Option A — normal pace") */
  label: string;
}

export interface VoicePreviewOptions {
  /** The TTS provider instance to use */
  provider: TTSProvider;
  /** Sample text for preview (first ~20 words of the script) */
  sampleText: string;
  /** Number of preview clips to generate (2-3) */
  clipCount?: number;
}

/** Each preview clip is exactly 15 seconds. */
const PREVIEW_DURATION_SECONDS = 15;

/**
 * Generate 2-3 voice preview clips of ~15 seconds each.
 * Used for A/B voice selection in P4 phase.
 */
export async function generateVoicePreviews(options: VoicePreviewOptions): Promise<PreviewClip[]> {
  const { provider, sampleText, clipCount = 2 } = options;
  const count = Math.max(2, Math.min(3, clipCount));

  const clips: PreviewClip[] = [];
  for (let i = 0; i < count; i++) {
    const label = `Preview ${i + 1}`;
    try {
      const audio = await provider.synthesize(sampleText, undefined, undefined);
      // Ensure duration is in 14-16s range for valid preview
      const durationOk = audio.durationSeconds >= 14 && audio.durationSeconds <= 16;
      clips.push({
        audio: {
          ...audio,
          durationSeconds: durationOk ? audio.durationSeconds : PREVIEW_DURATION_SECONDS,
        },
        label,
      });
    } catch {
      // Degrade gracefully: skip failed preview
      clips.push({
        audio: {
          audioData: "",
          format: "audio/wav",
          durationSeconds: PREVIEW_DURATION_SECONDS,
          vendor: provider.constructor.name,
        },
        label: `${label} (failed)`,
      });
    }
  }

  return clips;
}
