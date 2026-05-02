// [SPEC-F-101] AxisSpec auto-generator (TypeScript, frontend side).
// Pure deterministic function -- same input always produces same output.
// Mirrors the Python version in src/backend/services/axis_spec_generator.py.

export interface AxisSpecInput {
  data_points: Array<{ x: number | string; y: number }>;
  unit: string;
  granularity: "day" | "week" | "month" | "quarter" | "year" | "category";
}

export interface AxisSpecOutput {
  x_axis: {
    type: "time" | "category";
  };
  y_axis: {
    min: number;
    max: number;
    zero_based: boolean;
    tick_format: "0.01" | "1" | "1k" | "1M";
    unit_label: string;
  };
}

const TIME_GRANULARITIES = new Set([
  "day",
  "week",
  "month",
  "quarter",
  "year",
]);

function yValues(dataPoints: Array<{ x: number | string; y: number }>): number[] {
  return dataPoints.map((p) => p.y);
}

/**
 * Generate AxisSpec from data points + metadata.
 * Pure function: no side effects, no API calls, same input = same output.
 */
export function generateAxisSpec(input: AxisSpecInput): AxisSpecOutput {
  const { data_points, unit, granularity } = input;

  // --- x_axis type inference (AC-1) ---
  const xType: "time" | "category" = TIME_GRANULARITIES.has(granularity)
    ? "time"
    : "category";

  // --- y_axis range with 5% buffer (AC-2) ---
  const yVals = yValues(data_points);
  const dataMin = Math.min(...yVals);
  const dataMax = Math.max(...yVals);
  const buffer = (dataMax - dataMin) * 0.05;
  let yMin = dataMin - buffer;
  const yMax = dataMax + buffer;

  // --- zero_based heuristic (AC-3) ---
  // range_ratio = (dataMax - dataMin) / dataMax, 1 if dataMax is 0
  const rangeRatio = dataMax !== 0 ? (dataMax - dataMin) / dataMax : 1;
  const zeroBased = rangeRatio <= 0.5;
  if (zeroBased) {
    yMin = 0;
  }

  // --- tick_format auto-select (AC-4) ---
  const absMax = Math.max(Math.abs(yMin), Math.abs(yMax));
  let tickFormat: "0.01" | "1" | "1k" | "1M";
  if (absMax < 1) {
    tickFormat = "0.01";
  } else if (absMax < 1_000) {
    tickFormat = "1";
  } else if (absMax < 1_000_000) {
    tickFormat = "1k";
  } else {
    tickFormat = "1M";
  }

  return {
    x_axis: { type: xType },
    y_axis: {
      min: yMin,
      max: yMax,
      zero_based: zeroBased,
      tick_format: tickFormat,
      unit_label: unit,
    },
  };
}
