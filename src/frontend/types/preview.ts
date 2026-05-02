/**
 * SPEC-2.6 Phase Artifact Preview Types
 * Type contracts matching the SPEC-2.6 props table for P0-P11 preview components.
 */

// P0: Structured form view
export interface RequirementsJSON {
  [key: string]: unknown;
}

// P1/P3: Voice direction hint
export interface VoiceDirection {
  text: string;
  tone?: string;
  pace?: string;
  notes?: string;
}

// P2: Collapsible segment data
export interface KeyDataPoint {
  data_point_id: string;
  label: string;
  value: string | number;
  unit: string;
  source: string;
  trust_level: "user_verified" | "source_verified" | "llm_generated";
  segment_id: string;
  usage?: string;
  link?: string;
}

export interface ScriptSegment {
  id: string;
  content: string;
  key_data_points: KeyDataPoint[];
}

// P4: Audio segment for per-segment playback
export interface AudioSegment {
  id: string;
  audio_url: string;
  text: string;
  duration_sec: number;
  /** Characters per second rate (e.g. "4.0") */
  cps?: string;
  /** Segment status (e.g. "ready") */
  status?: string;
  /** Whether this segment has a speed/pacing warning */
  warn?: boolean;
}

// P5: Waveform audio data
export interface WaveformAudio {
  audio_url: string;
  duration_sec: number;
}

// P6: SFX trigger item
export interface SfxItem {
  type: string;
  time_sec: number;
  audio_url: string;
}

// P7: Storyboard shot
export interface StoryboardShot {
  id: string;
  description: string;
  duration_sec: number;
  template_id: string;
}

// P8: Video frame image
export interface VideoFrame {
  id: string;
  image_url: string;
  is_downgraded: boolean;
}

// P9: B-roll item
export interface BrollItem {
  id: string;
  thumbnail_url: string;
  source: string;
  is_placeholder: boolean;
}

// P10: Final video data
export interface FinalVideo {
  video_url: string;
  duration_sec: number;
  subtitles_url?: string;
}

// P11: Final distribution with covers and downloads
export interface Cover {
  url: string;
  aspect_ratio: string;
}

export interface FinalDistribution {
  video_url: string;
  covers: Cover[];
  download_urls: Record<string, string>;
}
