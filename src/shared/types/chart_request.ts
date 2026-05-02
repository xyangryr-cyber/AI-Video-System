// [SPEC-A-103] ChartRequest / AxisSpec / ChartStyleOverrides cross-language contract.
// Mirror of src/shared/schemas/chart_request.py +
//           src/shared/schemas/axis_spec.py +
//           src/shared/schemas/chart_style_overrides.py.
// Authority: docs/specs/SPEC-A-contracts.md §A-BDD-4 (SPEC-0A.11).

export type ChartType =
  | "line"
  | "bar"
  | "candlestick"
  | "pie"
  | "area"
  | "scatter";

export type ChartRequestStatus =
  | "awaiting_clarification"
  | "fetching"
  | "awaiting_verification"
  | "awaiting_confirmation"
  | "rendering"
  | "completed"
  | "failed";

export type TimeGranularity = "day" | "week" | "month" | "year";

export type XAxisType = "time" | "category" | "value";
export type YAxisType = "value" | "log";

export interface TimeRange {
  start: string;
  end: string;
  granularity: TimeGranularity;
}

export interface XAxisSpec {
  type: XAxisType;
  min?: unknown;
  max?: unknown;
  tick_format?: string;
  label: string;
}

export interface YAxisSpec {
  type: YAxisType;
  min?: number;
  max?: number;
  zero_based: boolean;
  unit: string;
  label: string;
}

export interface AxisSpec {
  x_axis: XAxisSpec;
  y_axis: YAxisSpec;
}

export interface ChartStyleOverrides {
  line_width?: number;
  line_color?: string;
  smooth?: boolean;
  background_color?: string;
  grid_visible?: boolean;
  show_source_label?: boolean;
  animation_duration_ms?: number;
}

export interface ChartRequest {
  request_id: string;
  user_intent: string;
  chart_type?: ChartType;
  entity?: string;
  time_range?: TimeRange;
  unit?: string;
  comparison_targets?: string[];
  status: ChartRequestStatus;
  pending_clarifications?: string[];
  fetched_data_ref?: string;
  axis_spec?: AxisSpec;
  style_overrides?: ChartStyleOverrides;
}
