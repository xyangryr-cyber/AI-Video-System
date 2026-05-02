// [SPEC-F-102] Render mode controller.
// Pure synchronous function: mode switch is local, no backend re-run.
// Shared data (data_points, axis_spec, style_overrides) is passed via
// TemplateProps and never forked between preview/production modes.

export type RenderMode = "preview" | "production";

export interface RenderConfig {
  width: number;
  height: number;
  fps: number;
  quality: number; // 0-100, higher for production
}

/**
 * Get render configuration based on mode.
 *
 * - preview: 480p (854x480), fps=1 (single frame), quality=50
 * - production: 1080p (1920x1080), fps=30 (full animation), quality=100
 *
 * Pure function: synchronous, no side effects, no API calls.
 * Same mode always produces the same config.
 */
export function getRenderConfig(mode: RenderMode): RenderConfig {
  if (mode === "preview") {
    return {
      width: 854,
      height: 480,
      fps: 1,        // single frame (AC-1)
      quality: 50,
    };
  }

  // production
  return {
    width: 1920,
    height: 1080,
    fps: 30,       // full animation (AC-2)
    quality: 100,
  };
}
