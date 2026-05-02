// [SPEC-F-010] Subtitle style configuration.
// Defines the subtitle_style fields per theme.json contract.

export interface SubtitleFont {
  family: string;
  size: number;
  weight: "normal" | "bold" | "light";
}

export interface SubtitleColor {
  text: string;
  highlight: string;
}

export interface SubtitleStroke {
  color: string;
  width: number;
}

export interface SubtitleBackground {
  color: string;
  opacity: number;
  padding: number;
  radius: number;
}

export interface SubtitlePosition {
  vertical: "top" | "center" | "bottom";
  horizontal: "left" | "center" | "right";
  margin_percent: number;
}

export type HighlightRuleType = "key_data_point" | "percentage" | "number" | "proper_noun";

export interface HighlightRule {
  type: HighlightRuleType;
  /** Priority: lower number = higher priority. key_data_point=0, percentage=1, number=2, proper_noun=3 */
  priority: number;
  color?: string;
  weight?: "normal" | "bold";
}

export interface SubtitleAnimation {
  type: "fade" | "slide_up" | "word_by_word" | "none";
  duration_ms: number;
}

export interface SubtitleStyle {
  font: SubtitleFont;
  color: SubtitleColor;
  stroke: SubtitleStroke;
  background: SubtitleBackground;
  position: SubtitlePosition;
  highlight_rules: HighlightRule[];
  animation: SubtitleAnimation;
}

/** Default subtitle_style theme values. */
export const DEFAULT_SUBTITLE_STYLE: SubtitleStyle = {
  font: {
    family: "Noto Sans SC, sans-serif",
    size: 28,
    weight: "bold",
  },
  color: {
    text: "#ffffff",
    highlight: "#FFD700",
  },
  stroke: {
    color: "#000000",
    width: 2,
  },
  background: {
    color: "#000000",
    opacity: 0.4,
    padding: 12,
    radius: 8,
  },
  position: {
    vertical: "bottom",
    horizontal: "center",
    margin_percent: 8,
  },
  highlight_rules: [
    { type: "key_data_point", priority: 0, weight: "bold" },
    { type: "percentage", priority: 1 },
    { type: "number", priority: 2 },
    { type: "proper_noun", priority: 3 },
  ],
  animation: {
    type: "word_by_word",
    duration_ms: 150,
  },
};
