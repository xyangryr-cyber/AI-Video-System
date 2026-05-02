import React, { useMemo } from "react";
import ReactECharts from "echarts-for-react";
import type { TemplateProps } from "@shared/types/template_props";

const AnimatedAreaChart: React.FC<TemplateProps> = ({ data, annotationKeyframes, theme }) => {
  const option = useMemo(() => {
    const raw = data as {
      xAxis: { data: string[] };
      series: { name: string; data: number[]; type: string }[];
    } | null;
    if (!raw) return {};

    const colorPalette = theme?.color_palette ?? [
      "#5470C6",
      "#91CC75",
      "#FAC858",
      "#EE6666",
      "#73C0DE",
    ];

    return {
      color: colorPalette,
      backgroundColor: theme?.background_color ?? "transparent",
      animation: true,
      animationDuration: 2000,
      tooltip: { trigger: "axis" },
      xAxis: {
        type: "category" as const,
        data: raw.xAxis?.data ?? [],
        axisLine: { lineStyle: { color: theme?.chart_style?.axis_color ?? "#ccc" } },
      },
      yAxis: {
        type: "value" as const,
        splitLine: { lineStyle: { color: theme?.chart_style?.grid_color ?? "#eee" } },
      },
      visualMap: {
        show: false,
        min: 0,
        max: (raw.series ?? []).reduce((m, s) => Math.max(m, ...s.data), 0),
        inRange: {
          color: [colorPalette[0] + "44", colorPalette[0] + "FF"],
        },
      },
      series: (raw.series ?? []).map((s, i) => ({
        name: s.name,
        type: "line" as const,
        data: s.data,
        smooth: true,
        symbol: "none",
        lineStyle: { width: 2 },
        areaStyle: {
          color: {
            type: "linear" as const,
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: colorPalette[i % colorPalette.length] + "AA" },
              { offset: 1, color: colorPalette[i % colorPalette.length] + "22" },
            ],
          },
        },
      })),
      legend: {
        data: (raw.series ?? []).map((s) => s.name),
        textStyle: { color: theme?.chart_style?.axis_color ?? "#666" },
      },
    };
  }, [data, annotationKeyframes, theme]);

  return <ReactECharts option={option} style={{ width: "100%", height: "100%" }} />;
};

export default AnimatedAreaChart;
