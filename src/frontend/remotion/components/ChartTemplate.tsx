// [SPEC-F-100] ChartTemplate -- accepts TemplateProps + optional ChartStyleOverrides.
// Priority: ChartStyleOverrides > theme_config > template default.
// Backward compatible with v3.15 TemplateProps (chart_style_overrides is optional).

import type { FC } from "react";
import type { ChartStyleOverrides } from "@shared/types/chart_request";
import type { TemplateProps } from "@shared/types/template_props";
import { mergeChartStyle, type MergedChartStyle } from "../utils/chart_style_merger";

export interface ChartTemplateProps extends TemplateProps {
  /** Optional ChartStyleOverrides for runtime style customization.
   *  When absent (undefined), rendering uses theme_config defaults
   *  with no breaking change to v3.15 callers. */
  chart_style_overrides?: ChartStyleOverrides;
  /** Whether the current source data is verified.
   *  Controls show_source_label rendering per AC-3. */
  source_verified?: boolean;
}

/**
 * ChartTemplate renders a chart with merged style.
 *
 * Backward compat: v3.15 callers pass TemplateProps only;
 * chart_style_overrides defaults to undefined and the component
 * falls back to theme_config defaults (zero breaking change).
 */
const ChartTemplate: FC<ChartTemplateProps> = (props) => {
  const { chart_style_overrides, theme, source_verified } = props;

  // Merge style: overrides > theme > template defaults (AC-1)
  const merged: MergedChartStyle = mergeChartStyle(chart_style_overrides, theme);

  // AC-3: show_source_label only when verified
  // The override requests the label, but we gate rendering on verified.
  const showLabel = merged.show_source_label && source_verified === true;

  return (
    <div className="chart-template" style={{ backgroundColor: merged.background_color }}>
      <svg width="100%" height="100%" viewBox="0 0 800 400" xmlns="http://www.w3.org/2000/svg">
        <rect x="0" y="0" width="800" height="400" fill={merged.background_color} />
        {merged.grid_visible && (
          <>
            <line
              x1="50"
              y1="50"
              x2="750"
              y2="50"
              stroke={theme.chart_style.grid_color}
              strokeWidth="0.5"
              strokeDasharray="4 4"
            />
            <line
              x1="50"
              y1="150"
              x2="750"
              y2="150"
              stroke={theme.chart_style.grid_color}
              strokeWidth="0.5"
              strokeDasharray="4 4"
            />
            <line
              x1="50"
              y1="250"
              x2="750"
              y2="250"
              stroke={theme.chart_style.grid_color}
              strokeWidth="0.5"
              strokeDasharray="4 4"
            />
            <line
              x1="50"
              y1="350"
              x2="750"
              y2="350"
              stroke={theme.chart_style.grid_color}
              strokeWidth="0.5"
              strokeDasharray="4 4"
            />
          </>
        )}
        <polyline
          points="100,300 200,200 300,250 400,100 500,150 600,80 700,180"
          fill="none"
          stroke={merged.line_color}
          strokeWidth={merged.line_width}
          strokeLinejoin="round"
          strokeLinecap="round"
        />
        {showLabel && (
          <text
            x="750"
            y="390"
            textAnchor="end"
            fontSize="10"
            fill={theme.chart_style.axis_color}
            opacity="0.6"
          >
            Source: Verified
          </text>
        )}
        <line
          x1="50"
          y1="50"
          x2="50"
          y2="360"
          stroke={theme.chart_style.axis_color}
          strokeWidth="1"
        />
        <line
          x1="50"
          y1="360"
          x2="750"
          y2="360"
          stroke={theme.chart_style.axis_color}
          strokeWidth="1"
        />
      </svg>
    </div>
  );
};

export default ChartTemplate;
