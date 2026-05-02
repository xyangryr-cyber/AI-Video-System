// ShotRenderInput — contract between shotRenderer.mjs and ShotComposition.tsx
// Mirrors the JSON structure passed via CLI --input and inputProps.

export interface ShotRenderInput {
  shot: {
    shot_id: string;
    template_type: string;
    content: Record<string, unknown>;
    time_range: { start_seconds: number; end_seconds: number };
  };
  templateType: string;
  durationInFrames: number;
  width: number;
  height: number;
  fps: number;
}
