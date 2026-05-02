// [SPEC-F-013] chart_material priority module.
// Chart-type templates call resolveChartData() to determine the effective
// data and axis configuration. Priority: chart_material > free-form data.
// When chart_material is present but data also carries conflicting chart
// content, a "chart_material_priority_violation" is logged and chart_material wins.
//
// ChartStyleOverrides (v3.15/v3.16) remain the authority for style
// (color/width/background); chart_material is the authority for data/axes.
// The two channels coexist without conflict per AC-6.

import type { ChartMaterial } from "@shared/types/chart_material";
import type { TemplateProps } from "@shared/types/template_props";

/** Chart types that MUST consume chart_material when present. */
const CHART_TEMPLATE_IDS = new Set([
  "animated_line_chart",
  "animated_bar_chart",
  "animated_pie_chart",
  "candlestick_chart",
  "event_timeline",
]);

export interface ResolvedChartData {
  /** The data to pass to the chart rendering engine.
   *  When chart_material is present this is derived from chart_spec;
   *  otherwise it is the raw TemplateProps.data. */
  data: unknown;
  /** Axis spec extracted from chart_material, if available. */
  axisSpec?: ChartMaterial["axis_spec"];
  /** The chart kind from chart_material, if available. */
  chartKind?: ChartMaterial["chart_spec"]["kind"];
  /** Whether chart_material was the source (true) or free-form data (false). */
  source: "chart_material" | "freeform_data";
}

/**
 * Resolve chart data with chart_material priority.
 *
 * When props.chart_material is present:
 *   1. chart_spec.series becomes the effective data
 *   2. axis_spec is passed through for axis configuration
 *   3. If props.data also looks like chart data (non-null object), a
 *      "chart_material_priority_violation" warning is logged
 *   4. chart_material always wins
 *
 * When props.chart_material is absent:
 *   Falls back to props.data (v3.15/v3.16 backward compat).
 */
export function resolveChartData(props: TemplateProps): ResolvedChartData {
  const { chart_material, data, templateId } = props;

  if (chart_material) {
    // Detect conflict: data carries chart content AND chart_material is present
    if (data !== null && typeof data === "object" && !Array.isArray(data)) {
      const dataObj = data as Record<string, unknown>;
      const hasChartKeys =
        "series" in dataObj ||
        "xAxis" in dataObj ||
        "yAxis" in dataObj ||
        "labels" in dataObj ||
        "ohlc" in dataObj ||
        "events" in dataObj;

      if (hasChartKeys) {
        console.warn(
          JSON.stringify({
            level: "WARN",
            event: "chart_material_priority_violation",
            templateId,
            msg: "chart_material present; ignoring conflicting free-form data",
          }),
        );
      }
    }

    return {
      data: chart_material.chart_spec.series,
      axisSpec: chart_material.axis_spec,
      chartKind: chart_material.chart_spec.kind,
      source: "chart_material",
    };
  }

  return {
    data,
    axisSpec: undefined,
    chartKind: undefined,
    source: "freeform_data",
  };
}

/**
 * Validate that a chart-type template has chart_material when expected.
 *
 * Chart templates (line/bar/pie/candlestick/event_timeline) SHOULD have
 * chart_material from P7A. When missing, logs an error per AC-4.
 * Non-chart templates are not expected to carry chart_material.
 *
 * @returns true if validation passes (chart_material present or not a chart template)
 */
export function validateChartMaterial(props: TemplateProps): boolean {
  const { chart_material, templateId } = props;

  if (CHART_TEMPLATE_IDS.has(templateId) && !chart_material) {
    console.error(
      JSON.stringify({
        level: "ERROR",
        event: "chart_material_missing",
        templateId,
        msg: "chart-type template missing chart_material — rendering from free-form data may produce incorrect results",
      }),
    );
    return false;
  }

  return true;
}
