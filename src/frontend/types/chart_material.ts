// [SPEC-E-015] ChartMaterialView — frontend View type mirroring ChartMaterial.
// Keep in lockstep with src/shared/types/chart_material.ts and SPEC-A-016.
export type Granularity = "day" | "week" | "month";

export type ChartKind = "line" | "bar" | "pie";

export type XAxisType = "time" | "category" | "value";

export type ScaleMode = "linear" | "log";

export interface DateRange {
  start: string;
  end: string;
}

export interface ChartSource {
  provider: string;
  symbol: string;
}

export interface ChartSpec {
  kind: ChartKind;
  series: unknown[];
}

export interface XAxis {
  type: XAxisType;
  labels: unknown[];
  range: [unknown, unknown];
}

export interface YAxis {
  unit: string;
  min: number;
  max: number;
  scale_mode: ScaleMode;
}

export interface AxisSpec {
  x_axis: XAxis;
  y_axis: YAxis;
}

export interface ChartMaterialView {
  chart_id: string;
  shot_id: string;
  metric_name: string;
  date_range: DateRange;
  granularity: Granularity;
  source: ChartSource;
  verification_status: "verified";
  chart_spec: ChartSpec;
  axis_spec: AxisSpec;
}
