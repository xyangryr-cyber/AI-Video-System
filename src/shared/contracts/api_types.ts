// Auto-generated API types for TypeScript SDK.
// Source: src/shared/schemas/*.py (mirrored contract types)

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type OkResponse = Record<string, any>;

export interface CreateProjectRequest {
  title: string;
  description?: string;
}

export interface CreateProjectResponse {
  project_id: string;
}

export interface ProjectInfo {
  id: string;
  title: string;
  description: string;
  phase: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectListResponse {
  projects: ProjectInfo[];
  total: number;
}

export interface ProjectState {
  phase: number;
  status: string;
  artifacts: Record<string, unknown>;
}

export interface AdvanceRequest {
  phase?: number;
}

export interface AdvanceResponse {
  phase: number;
  status: string;
}

export interface RollbackRequest {
  target_phase: number;
}

export interface RollbackResponse {
  phase: number;
  status: string;
}

export interface SkipResponse {
  phase: number;
  status: string;
}

export interface ChatRequest {
  message: string;
}

export interface ChatResponse {
  reply: string;
  action?: string;
}

export interface ArtifactEnvelope {
  phase: number;
  data: unknown;
}

export interface EventsResponse {
  events: unknown[];
}

export interface CostsResponse {
  total_cost_usd: number;
  by_phase: Record<string, number>;
}

export interface TaskListResponse {
  tasks: unknown[];
}

export interface Preferences {
  [key: string]: unknown;
}

export interface PreferencesResponse {
  preferences: Preferences;
}

export interface PreferencesUpdateRequest {
  preferences: Preferences;
}

export interface PreferencesUpdateResponse {
  preferences: Preferences;
}

export interface PreferencesConfirmRequest {
  confirmed: boolean;
}

export interface PreferencesConfirmResponse {
  status: string;
}

export interface SnapshotListResponse {
  snapshots: unknown[];
}

export interface SnapshotRollbackResponse {
  status: string;
}

export interface ModelConfig {
  provider: string;
  model: string;
}

export interface BrandKit {
  logo_url?: string;
  primary_color?: string;
  secondary_color?: string;
  font_family?: string;
}

export interface SettingsResponse {
  model_config: ModelConfig;
  brand_kit: BrandKit;
}

export interface SystemStatus {
  status: string;
  uptime_seconds: number;
}

export interface WsEventEnvelope {
  type: string;
  project_id: string;
  payload: unknown;
}
