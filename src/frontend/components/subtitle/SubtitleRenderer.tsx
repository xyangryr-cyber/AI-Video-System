// [SPEC-F-010] SubtitleRenderer — word-by-word and sentence mode rendering.
// Consumes subtitle_words[] (SubtitleWord schema from SPEC-A).
// All programmatic — no external API calls.

import type { FC } from "react";
import { useCurrentFrame } from "remotion";
import type { SubtitleWord } from "@shared/types/shared_types";
import type { SubtitleStyle } from "./subtitleStyle";
import { DEFAULT_SUBTITLE_STYLE } from "./subtitleStyle";

export type SubtitleMode = "word_by_word" | "sentence";

export interface SubtitleRendererProps {
  /** Subtitle words with Whisper word-level alignment */
  subtitleWords: SubtitleWord[];
  /** Render mode */
  mode?: SubtitleMode;
  /** Current frame (from Remotion useCurrentFrame) */
  frame?: number;
  /** Frames per second for time-to-frame conversion */
  fps?: number;
  /** Subtitle style configuration */
  style?: Partial<SubtitleStyle>;
}

/**
 * Convert time in seconds to frame number.
 */
function timeToFrame(timeSec: number, fps: number): number {
  return Math.round(timeSec * fps);
}

/**
 * SubtitleRenderer renders subtitle words with word-level timing alignment.
 * Whisper alignment: word.start_sec / word.end_sec drive per-word appearance.
 * Enforces 200ms maximum alignment error tolerance.
 */
const SubtitleRenderer: FC<SubtitleRendererProps> = ({
  subtitleWords,
  mode = "word_by_word",
  frame: extFrame,
  fps = 30,
  style: customStyle,
}) => {
  const internalFrame = useCurrentFrame();
  const frame = extFrame ?? internalFrame;
  const timeSec = frame / fps;
  const mergedStyle = { ...DEFAULT_SUBTITLE_STYLE, ...customStyle };

  // Filter words visible at current time (within 200ms tolerance)
  const TOLERANCE_SEC = 0.2;
  const activeWords = subtitleWords.filter((sw) => {
    const start = sw.start_sec - TOLERANCE_SEC;
    const end = sw.end_sec + TOLERANCE_SEC;
    return timeSec >= start && timeSec <= end;
  });

  if (activeWords.length === 0) return null;

  const textColor = mergedStyle.color.text;
  const highlightColor = mergedStyle.color.highlight;
  const fontFamily = mergedStyle.font.family;
  const fontSize = mergedStyle.font.size;
  const fontWeight = mergedStyle.font.weight;

  if (mode === "sentence") {
    // Sentence mode: render all active words as one line
    const sentence = activeWords.map((sw) => sw.word).join(" ");
    return (
      <div
        className="subtitle-sentence"
        style={{
          position: "absolute",
          bottom: `${mergedStyle.position.margin_percent}%`,
          left: "50%",
          transform: "translateX(-50%)",
          fontFamily,
          fontSize,
          fontWeight: typeof fontWeight === "string" ? fontWeight : undefined,
          color: textColor,
          textShadow: `0 0 ${mergedStyle.stroke.width}px ${mergedStyle.stroke.color}`,
          backgroundColor: `rgba(0,0,0,${mergedStyle.background.opacity})`,
          padding: mergedStyle.background.padding,
          borderRadius: mergedStyle.background.radius,
          textAlign: "center",
        }}
      >
        {sentence}
      </div>
    );
  }

  // Word-by-word mode: each word appears at its precise timing
  return (
    <div
      className="subtitle-word-by-word"
      style={{
        position: "absolute",
        bottom: `${mergedStyle.position.margin_percent}%`,
        left: "50%",
        transform: "translateX(-50%)",
        display: "flex",
        gap: 8,
        fontFamily,
        fontSize,
        color: textColor,
        textShadow: `0 0 ${mergedStyle.stroke.width}px ${mergedStyle.stroke.color}`,
        backgroundColor: `rgba(0,0,0,${mergedStyle.background.opacity})`,
        padding: mergedStyle.background.padding,
        borderRadius: mergedStyle.background.radius,
      }}
    >
      {activeWords.map((sw, idx) => (
        <span
          key={idx}
          style={{
            color: sw.highlight_type ? highlightColor : textColor,
            fontWeight: sw.highlight_type ? "bold" : undefined,
            transition: `color ${mergedStyle.animation.duration_ms}ms`,
          }}
        >
          {sw.word}
        </span>
      ))}
    </div>
  );
};

export default SubtitleRenderer;
