// [SPEC-F-100] ChartStyleOverrides merge utility.
// Priority: ChartStyleOverrides > theme_config > template default.
// Per-field independent override: unset fields do not clobber lower layers.

import type { ChartStyleOverrides } from "@shared/types/chart_request";
import type { ThemeConfig } from "@shared/types/shared_types";

export interface MergedChartStyle {
  line_color: string;
  line_width: number;
  background_color: string;
  grid_visible: boolean;
  show_source_label: boolean;
  smooth: boolean;
}

const TEMPLATE_DEFAULTS: MergedChartStyle = {
  line_color: "#0044cc",
  line_width: 2,
  background_color: "#ffffff",
  grid_visible: true,
  show_source_label: false,
  smooth: false,
};

/**
 * Build a structured log entry for invalid palette colors.
 * Must match the shape expected by the palette_fallback log event.
 */
function logPaletteFallback(
  field: string,
  requested: string,
  applied: string,
): void {
  const entry = {
    level: "WARN",
    event: "color.palette_fallback",
    field,
    requested,
    applied,
  };
  console.warn(JSON.stringify(entry));
}

/**
 * Validate a color against the theme palette. Returns palette[0] if invalid,
 * with a structured log entry.
 */
function resolveColor(
  overrideColor: string | undefined,
  themeColor: string | undefined,
  defaultColor: string,
  palette: string[],
): string {
  let chosen = overrideColor ?? themeColor ?? defaultColor;
  if (palette.length > 0 && !palette.includes(chosen)) {
    logPaletteFallback("line_color", chosen, palette[0]);
    chosen = palette[0];
  }
  return chosen;
}

/**
 * Merge ChartStyleOverrides + ThemeConfig + template defaults.
 *
 * @param overrides   Runtime user overrides (optional -- backward compat).
 * @param theme       ThemeConfig (includes color_palette, chart_style, etc.).
 * @returns           Resolved MergedChartStyle.
 */
export function mergeChartStyle(
  overrides: ChartStyleOverrides | undefined,
  theme: ThemeConfig,
): MergedChartStyle {
  const palette = theme.color_palette ?? [];

  const line_color = resolveColor(
    overrides?.line_color,
    palette[0],
    TEMPLATE_DEFAULTS.line_color,
    palette,
  );

  const line_width =
    overrides?.line_width ?? TEMPLATE_DEFAULTS.line_width;

  const background_color =
    overrides?.background_color ?? theme.background_color ?? TEMPLATE_DEFAULTS.background_color;

  const grid_visible =
    overrides?.grid_visible ?? TEMPLATE_DEFAULTS.grid_visible;

  const smooth = overrides?.smooth ?? TEMPLATE_DEFAULTS.smooth;

  // show_source_label: returns the override value (or template default).
  // The caller gates rendering on verified status per AC-3:
  // show_source_label is only rendered when verified === true.
  const show_source_label =
    overrides?.show_source_label ?? TEMPLATE_DEFAULTS.show_source_label;

  return {
    line_color,
    line_width,
    background_color,
    grid_visible,
    show_source_label,
    smooth,
  };
}
