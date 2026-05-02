// Cross-module shared types (SPEC-0A.6, SPEC-0A.7).
// Mirror of src/shared/schemas/shared_types.py. Any other module that needs
// these concepts MUST import from this file rather than redefining them.

export type TrustLevel = "user_verified" | "source_verified" | "llm_generated";

export interface KeyDataPoint {
  data_point_id: string; // 'dp_' + suffix
  label: string;
  value: string | number;
  unit: string;
  source: string;
  trust_level: TrustLevel;
  segment_id: string;
  usage?: string;
  link?: string;
}

export interface VoiceParams {
  voice_id: string;
  style: string;
  style_degree: number; // [0.01, 2.0]
  rate_wpm: number;
  pitch: number;
  volume: number;
}

export interface SegmentVoiceOverrides {
  rate_multiplier: number; // [0.8, 1.2]
  emotion: string;
  style_degree: number;
  emphasis_words: string[];
  volume: number;
}

export type HighlightType = "key_data" | "percentage" | "number" | "proper_noun" | null;

export interface SubtitleWord {
  word: string;
  start_sec: number;
  end_sec: number;
  highlight_type: HighlightType;
}

export type DiscreteAction = "highlight" | "zoom_in" | "zoom_out" | "annotate" | "dim" | "reset";

export interface DiscreteKeyframe {
  type: "discrete";
  time_offset_sec: number;
  at_frame?: number;
  action: DiscreteAction;
  target: string;
  annotation?: string;
}

export type ContinuousEasing = "linear" | "ease_in" | "ease_out" | "ease_in_out";

export interface ProgressMapping {
  progress: number;
  data_index: number;
  label?: string;
}

export interface PauseTrigger {
  at_progress: number;
  at_frame?: number;
  duration_sec: number;
  narration_keyword: string;
  action: string;
  target_data_range?: [number, number];
}

export interface ContinuousKeyframe {
  type: "continuous";
  start_sec: number;
  end_sec: number;
  start_frame?: number;
  end_frame?: number;
  easing: ContinuousEasing;
  progress_mapping: ProgressMapping[];
  pause_triggers?: PauseTrigger[];
}

export type AnnotationKeyframe = DiscreteKeyframe | ContinuousKeyframe;

export interface ThemeChartStyle {
  axis_color: string;
  grid_color: string;
  background_color?: string;
  label_font_size: number;
  tooltip_style: Record<string, unknown>;
}

export interface ThemeConfig {
  color_palette: string[];
  background_color: string;
  font_family: string;
  chart_style: ThemeChartStyle;
  subtitle_style: Record<string, unknown>;
}

// SPEC-0A.6 style_lock state ownership (documentation-as-code).
export const STYLE_LOCK_OWNERSHIP = {
  storage_field: "phases.style_lock_path",
  file_path_template: "data/projects/{project_id}/phase_7/style_lock.json",
  write_agent: "StoryboardAgent",
  write_phase: 7,
  write_api: "POST /api/projects/{id}/preferences/confirm",
  read_agents: ["KeyframeRenderAgent", "ThemeConfig"] as const,
  read_phase: 8,
  read_api: "GET /api/projects/{id}/phases/7/artifact",
  unlock_api: "POST /api/projects/{id}/rollback",
} as const;
