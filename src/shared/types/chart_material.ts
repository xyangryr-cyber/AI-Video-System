// [SPEC-A-016] ChartMaterial types (TypeScript mirror).
// Authority: docs/specs/SPEC_REVISION_REQ_v3.17_2026-04-17.md A-AUDP7A-4.
//
// Keep in lockstep with src/shared/schemas/chart_material.py and
// schemas/chart_material.schema.json.
//
// Relationship to v3.16 ChartRequest (SPEC-0A.11): this is the P7A-exit /
// P8-entry downstream contract, 1:1 with ChartRequest via the derivation
//   chart_id := "chart_" + numeric_suffix(request_id)
// See derive_chart_id_from_request_id / derive_request_id_from_chart_id
// in chart_material.py for the canonical rule.

export type Granularity = "day" | "week" | "month";

export type ChartKind = "line" | "bar" | "pie";

export type XAxisType = "time" | "category" | "value";

export type ScaleMode = "linear" | "log";

export interface DateRange {
  start: string; // ISO-8601 date (YYYY-MM-DD)
  end: string; // ISO-8601 date (YYYY-MM-DD)
}

export interface ChartSource {
  provider: string;
  symbol: string;
}

export interface ChartSpec {
  kind: ChartKind;
  series: unknown[]; // per-kind schema is defined in the consuming template
}

export interface XAxis {
  type: XAxisType;
  labels: unknown[];
  range: [unknown, unknown]; // length === 2
}

export interface YAxis {
  unit: string;
  min: number;
  max: number; // invariant: min < max (enforced by Pydantic + L1 check)
  scale_mode: ScaleMode;
}

export interface AxisSpec {
  x_axis: XAxis;
  y_axis: YAxis;
}

export interface ChartMaterial {
  chart_id: string; // ^chart_\d{3,}$
  shot_id: string; // ^shot_\d{2,}$
  metric_name: string;
  date_range: DateRange;
  granularity: Granularity;
  source: ChartSource;
  verification_status: "verified"; // const: ChartMaterial only exists once verified
  chart_spec: ChartSpec;
  axis_spec: AxisSpec;
}
