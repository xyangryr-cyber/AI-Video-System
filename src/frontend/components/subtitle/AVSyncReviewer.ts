// [SPEC-F-010] AVSyncReviewer — L1 programmatic AV sync check.
// Checks: AV offset <100ms, subtitle alignment <200ms, blank frames, highlight vs key_data_point consistency.
// Zero external API calls — purely programmatic.

import type { SubtitleWord } from "@shared/types/shared_types";
import { checkKeyDataPointConsistency } from "./subtitleHighlighter";

export interface AVSyncResult {
  pass: boolean;
  failures: AVSyncFailure[];
}

export interface AVSyncFailure {
  type: "av_offset" | "subtitle_alignment" | "blank_frame" | "highlight_mismatch";
  detail: string;
  /** Affected time in seconds */
  at_sec?: number;
}

const MAX_AV_OFFSET_MS = 100;
const MAX_SUBTITLE_ALIGNMENT_MS = 200;

/**
 * Review subtitle words for AV sync issues.
 *
 * Checks:
 * - Subtitle words alignment error < 200ms
 * - AV offset < 100ms (from audio_start_sec)
 * - Highlight word vs key_data_point consistency
 */
export function reviewSubtitleSync(
  subtitleWords: SubtitleWord[],
  audioStartSec: number,
  keyDataPointValue?: string | number,
): AVSyncResult {
  const failures: AVSyncFailure[] = [];

  for (const sw of subtitleWords) {
    // Check word-level alignment error (< 200ms)
    const wordDurationMs = (sw.end_sec - sw.start_sec) * 1000;
    const alignmentOffsetMs = Math.abs(sw.start_sec - audioStartSec) * 1000;

    // Subtitle alignment check
    if (alignmentOffsetMs > MAX_SUBTITLE_ALIGNMENT_MS) {
      failures.push({
        type: "subtitle_alignment",
        detail: `word '${sw.word}' alignment offset ${alignmentOffsetMs.toFixed(
          0,
        )}ms exceeds ${MAX_SUBTITLE_ALIGNMENT_MS}ms`,
        at_sec: sw.start_sec,
      });
    }

    // AV offset check (first word relative to audio start)
    if (alignmentOffsetMs > MAX_AV_OFFSET_MS) {
      failures.push({
        type: "av_offset",
        detail: `AV offset ${alignmentOffsetMs.toFixed(0)}ms exceeds ${MAX_AV_OFFSET_MS}ms`,
        at_sec: sw.start_sec,
      });
    }

    // Highlight word vs key_data_point consistency
    if (sw.highlight_type && keyDataPointValue !== undefined) {
      const consistent = checkKeyDataPointConsistency(
        sw.word,
        sw.highlight_type as Parameters<typeof checkKeyDataPointConsistency>[1],
        keyDataPointValue,
      );
      if (!consistent) {
        failures.push({
          type: "highlight_mismatch",
          detail: `highlight word '${sw.word}' value inconsistent with key_data_point '${keyDataPointValue}'`,
          at_sec: sw.start_sec,
        });
      }
    }
  }

  return {
    pass: failures.length === 0,
    failures,
  };
}

/**
 * Check for blank frames in a subtitle sequence.
 * Returns FAIL if any blank frames are detected.
 */
export function checkBlankFrames(
  subtitleWords: SubtitleWord[],
  totalDurationSec: number,
  fps: number = 30,
): AVSyncFailure[] {
  const failures: AVSyncFailure[] = [];
  const totalFrames = Math.round(totalDurationSec * fps);
  const coveredFrames = new Set<number>();

  for (const sw of subtitleWords) {
    const startFrame = Math.round(sw.start_sec * fps);
    const endFrame = Math.round(sw.end_sec * fps);
    for (let f = startFrame; f <= endFrame; f++) {
      coveredFrames.add(f);
    }
  }

  // Check for gaps between subtitle words
  if (subtitleWords.length > 0) {
    let lastEnd = subtitleWords[0].end_sec;
    for (let i = 1; i < subtitleWords.length; i++) {
      const gap = subtitleWords[i].start_sec - lastEnd;
      if (gap > 0) {
        // Gap detected — consecutive words have space between them
        // This is normal; blank frames are about truly empty video, not inter-word gaps
      }
      lastEnd = subtitleWords[i].end_sec;
    }
  }

  // Actual blank frame check: are there periods with zero active words?
  // A blank frame occurs when no subtitle word covers a frame but there should be content.
  for (let f = 0; f < totalFrames; f++) {
    if (!coveredFrames.has(f)) {
      const timeSec = f / fps;
      // Check if this frame is truly "blank" — no subtitle content at all
      let hasActiveWord = false;
      for (const sw of subtitleWords) {
        if (timeSec >= sw.start_sec && timeSec <= sw.end_sec) {
          hasActiveWord = true;
          break;
        }
      }
      if (!hasActiveWord) {
        failures.push({
          type: "blank_frame",
          detail: `blank frame at frame ${f} (${timeSec.toFixed(2)}s)`,
          at_sec: timeSec,
        });
        break; // one blank frame is enough to FAIL per AC-8
      }
    }
  }

  return failures;
}
