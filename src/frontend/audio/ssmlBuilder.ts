// SPEC-F-008 SSML Builder
// Pure functions — zero LLM calls, deterministic only.

import type { SegmentVoiceOverrides, SubtitleWord } from "@shared/types/shared_types";

export interface SegmentEntry {
  id: string;
  text: string;
  voiceOverrides: SegmentVoiceOverrides;
  words?: SubtitleWord[];
}

export interface SsmlResult {
  ssml: string;
}

/**
 * Emotion transition pairs that trigger an 800ms break.
 * Key: previous emotion → current emotion.
 */
const EMOTION_TRANSITION_BREAKS: Record<string, Set<string>> = {
  sad: new Set(["excited", "happy", "angry"]),
  excited: new Set(["sad", "calm"]),
  calm: new Set(["excited", "angry"]),
  angry: new Set(["calm", "sad"]),
};

const EMOTION_BREAK_MS = 800;

/**
 * Check if a sentence is numeric-dense.
 * Numeric-dense: >= 15% of characters are digits or numeric symbols (%, ., ,).
 */
export function isNumericDense(text: string, threshold = 0.15): boolean {
  if (text.length === 0) return false;
  const numericCount = (text.match(/[\d%.,]/g) ?? []).length;
  return numericCount / text.length >= threshold;
}

/**
 * Build SSML from a list of segments with voice overrides.
 * Handles:
 * - Emotion transitions → 800ms <break>
 * - Numeric-dense sentences → <prosody rate="slow">
 * - Emphasis words → <emphasis>
 */
export function buildSSML(segments: SegmentEntry[]): SsmlResult {
  const parts: string[] = ['<speak xmlns="http://www.w3.org/2001/10/synthesis">'];

  for (let i = 0; i < segments.length; i++) {
    const current = segments[i];
    const prev = i > 0 ? segments[i - 1] : null;

    // Emotion transition break
    if (prev) {
      const prevEmotion = prev.voiceOverrides.emotion;
      const currEmotion = current.voiceOverrides.emotion;
      const transitions = EMOTION_TRANSITION_BREAKS[prevEmotion];
      if (transitions && transitions.has(currEmotion)) {
        parts.push(`<break time="${EMOTION_BREAK_MS}ms"/>`);
      }
    }

    const rate =
      current.voiceOverrides.rate_multiplier !== 1.0
        ? ` rate="${current.voiceOverrides.rate_multiplier}"`
        : "";

    const volume = current.voiceOverrides.volume;

    if (isNumericDense(current.text)) {
      parts.push(`<prosody rate="slow" volume="${volume}">`);
    } else {
      parts.push(`<prosody${rate} volume="${volume}">`);
    }

    // Emphasis words
    const emphasisWords = new Set(current.voiceOverrides.emphasis_words);
    if (emphasisWords.size > 0) {
      const textWithEmphasis = current.text.replace(
        new RegExp(`\\b(${[...emphasisWords].join("|")})\\b`, "gi"),
        '<emphasis level="moderate">$1</emphasis>',
      );
      parts.push(textWithEmphasis);
    } else {
      parts.push(current.text);
    }

    parts.push("</prosody>");
  }

  parts.push("</speak>");
  return { ssml: parts.join("") };
}

/**
 * Generate SSML segments from a list of segment texts and voice overrides.
 */
export function segmentsToSSML(segments: SegmentEntry[]): SsmlResult {
  return buildSSML(segments);
}
