// Shared artifact types (SPEC-0A.1). Mirror of src/shared/schemas/artifacts.py.

export type DurationClass = "short" | "medium" | "long";
export type NarrativeTemplate =
  | "chronological"
  | "progressive"
  | "comparative"
  | "problem_solution"
  | "storytelling";
export type SubtitleStyle = "word_by_word" | "sentence";
export type LockedBy = "user_confirmed" | "auto_recommended";

export interface TargetDuration {
  min_sec: number;
  max_sec: number;
}

export interface TargetWordCount {
  min: number;
  max: number;
}

export interface Category {
  level1: string;
  level2: string;
}

export type PlatformRole = "primary" | "secondary";

export interface PlatformEntry {
  platform: string;
  role: PlatformRole;
}

export interface VoicePreferences {
  voice_id: string;
  style: string;
}

export interface SubtitlePreferences {
  style: SubtitleStyle;
  highlight_enabled: boolean;
}

export interface Requirements {
  project_id: string;
  title: string;
  topic: string;
  clarified_topic: string;
  duration_class: DurationClass;
  target_duration_seconds: number;
  target_duration: TargetDuration;
  target_word_count: TargetWordCount;
  platform: PlatformEntry[];
  category: Category;
  narrative_template: NarrativeTemplate;
  voice_preferences: VoicePreferences;
  subtitle_preferences: SubtitlePreferences;
  target_platform: string;
  clarification_needed: Array<Record<string, string>>;
}

export interface VoiceParams {
  rate_multiplier: number;
  emotion: string;
}

export interface TimelineSegment {
  segment_id: string;
  text: string;
  start_sec: number;
  end_sec: number;
  audio_path: string;
  voice_params: VoiceParams;
  word_count: number;
}

export interface Timeline {
  segments: TimelineSegment[];
  total_duration_sec: number;
  sample_rate: number;
}

export interface ColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
}

export interface ChartStyle {
  axis_color: string;
  grid_color: string;
  label_font_size: number;
}

export interface StyleLock {
  project_id: string;
  locked_at: string;
  locked_by: LockedBy;
  color_palette: ColorPalette;
  font_family: string;
  chart_style: ChartStyle;
}

export interface PolishedScriptArtifact {
  style_applied?: string;
}

export interface AnnotationSpan {
  span_id: string;
  text_range: [number, number];
  effect: string;
  rationale: string;
  narrative_role: string;
}

export type AssetStatus = "not_needed" | "fetched";

export interface AssetSourcingEntry {
  shot_id: string;
  status: AssetStatus;
  need?: string;
  action?: string;
  data?: Record<string, unknown>;
}

export type RenderStatus = "pending_broll" | "rendered";

export interface KeyframeRenderEntry {
  shot_id: string;
  render_status: RenderStatus;
  file_name?: string;
  thumbnail_url?: string;
}

export interface BRollEntry {
  file_name: string;
  duration_sec: number;
  match_label: string;
  license: string;
  source_url?: string;
}

export interface DeliveryVariant {
  platform: string;
  resolution: string;
  codec: string;
  aspect_ratio: string;
  file_size_mb: number;
  download_url: string;
}

export interface SubtitleDownload {
  format: string;
  download_url: string;
}
