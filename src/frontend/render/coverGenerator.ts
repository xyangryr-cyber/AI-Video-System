// [SPEC-F-011] Cover generator — 3 templates x 3 aspect ratios = 9 covers.
// Data sources: key_data_point for big numbers, theme for styling.

export type CoverTemplate = "data_focus" | "chart_preview" | "clean_text";

export type AspectRatio = "16:9" | "3:4" | "1:1";

export interface CoverDimensions {
  width: number;
  height: number;
}

export interface CoverConfig {
  template: CoverTemplate;
  ratio: AspectRatio;
  dimensions: CoverDimensions;
  /** Big number from key_data_point for data_focus template */
  keyDataPointValue?: number;
  /** Unit label for the key data point */
  unit?: string;
}

export interface CoverResult {
  template: CoverTemplate;
  ratio: AspectRatio;
  path: string;
  width: number;
  height: number;
}

/** Aspect ratio dimension lookup. */
export const ASPECT_DIMENSIONS: Record<AspectRatio, CoverDimensions> = {
  "16:9": { width: 1280, height: 720 },
  "3:4": { width: 540, height: 720 },
  "1:1": { width: 720, height: 720 },
};

const ALL_TEMPLATES: CoverTemplate[] = ["data_focus", "chart_preview", "clean_text"];
const ALL_RATIOS: AspectRatio[] = ["16:9", "3:4", "1:1"];

/**
 * Generate all 9 covers (3 templates x 3 ratios).
 * Returns an array of 9 CoverResult objects.
 */
export function generateAllCovers(
  keyDataPointValue?: number,
  unit?: string
): CoverResult[] {
  const covers: CoverResult[] = [];

  for (const template of ALL_TEMPLATES) {
    for (const ratio of ALL_RATIOS) {
      const dimensions = ASPECT_DIMENSIONS[ratio];
      const suffix = `${template}_${ratio.replace(":", "x")}`;
      covers.push({
        template,
        ratio,
        path: `phase_11/covers/${suffix}.png`,
        width: dimensions.width,
        height: dimensions.height,
      });
    }
  }

  return covers;
}

/**
 * Generate a single cover for a specific template and ratio.
 * data_focus sources its big number from key_data_point.
 */
export function generateCover(config: CoverConfig): CoverResult {
  const dims = ASPECT_DIMENSIONS[config.ratio];
  const suffix = `${config.template}_${config.ratio.replace(":", "x")}`;

  return {
    template: config.template,
    ratio: config.ratio,
    path: `phase_11/covers/${suffix}.png`,
    width: dims.width,
    height: dims.height,
  };
}
