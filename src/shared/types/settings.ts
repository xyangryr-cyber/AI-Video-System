// Settings, Preferences & Snapshot API TypeScript types (SPEC-0A.4).
// Mirror of src/shared/schemas/settings.py.

import type { BrandKit } from "./brand_kit";

export interface SettingsResponse {
  model_config_data: Record<string, unknown>;
  brand_kit: BrandKit;
}

export interface PreferencesResponse {
  global_rules_md: string;
  user_preferences_md: string;
}

export interface PreferencesUpdateRequest {
  global_rules_md?: string;
  user_preferences_md?: string;
}

export interface SnapshotItem {
  id: string;
  created_at: string;
  preview: string;
}

export interface SnapshotListResponse {
  snapshots: SnapshotItem[];
}
