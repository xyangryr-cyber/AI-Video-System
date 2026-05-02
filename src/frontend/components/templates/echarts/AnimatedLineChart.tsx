import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { TemplateProps } from '@shared/types/template_props';
import {
  resolveChartData,
  validateChartMaterial,
} from '@frontend/render/chart_material_priority';

const AnimatedLineChart: React.FC<TemplateProps> = (props) => {
  const { annotationKeyframes, theme, chart_material } = props;

  const option = useMemo(() => {
    validateChartMaterial(props);
    const resolved = resolveChartData(props);

    const colorPalette = theme?.color_palette ?? [
      '#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE',
    ];

    // When chart_material provides axis_spec, use it for axis config
    const axisSpec = resolved.axisSpec;
    const resolvedData = resolved.data;

    let xData: string[] = [];
    let seriesData: { name: string; data: number[]; type: string }[] = [];

    if (resolved.source === "chart_material" && Array.isArray(resolvedData)) {
      // chart_material: series is { name, data }[]
      seriesData = (resolvedData as { name: string; data: number[] }[]).map(
        (s) => ({ ...s, type: "line" as const }),
      );
      if (axisSpec) {
        xData = (axisSpec.x_axis.labels ?? []) as string[];
      }
    } else {
      const raw = resolved.data as {
        xAxis: { data: string[] };
        series: { name: string; data: number[]; type: string }[];
      } | null;
      if (!raw) return {};
      xData = raw.xAxis?.data ?? [];
      seriesData = (raw.series ?? []).map((s) => ({
        name: s.name,
        type: 'line' as const,
        data: s.data,
      }));
    }

    const yAxisMin = axisSpec?.y_axis?.min;
    const yAxisMax = axisSpec?.y_axis?.max;

    return {
      color: colorPalette,
      backgroundColor: theme?.background_color ?? 'transparent',
      animation: true,
      animationDuration: 1500,
      animationDelay(idx: number) {
        return idx * 200;
      },
      tooltip: { trigger: 'axis' },
      xAxis: {
        type: 'category' as const,
        data: xData,
        axisLine: { lineStyle: { color: theme?.chart_style?.axis_color ?? '#ccc' } },
      },
      yAxis: {
        type: 'value' as const,
        ...(yAxisMin !== undefined ? { min: yAxisMin } : {}),
        ...(yAxisMax !== undefined ? { max: yAxisMax } : {}),
        splitLine: { lineStyle: { color: theme?.chart_style?.grid_color ?? '#eee' } },
      },
      graphic: (annotationKeyframes ?? []).length > 0
        ? annotationKeyframes
            .filter((kf) => kf.type === 'discrete')
            .map((kf) => ({
              type: 'text' as const,
              left: 'center',
              top: 30,
              style: {
                text: (kf as { annotation?: string }).annotation ?? '',
                fill: colorPalette[0],
                fontSize: 14,
              },
            }))
        : [],
      series: seriesData.map((s, _i) => ({
        name: s.name,
        type: 'line' as const,
        data: s.data,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { width: 2 },
        markPoint: {
          data: [
            { type: 'max' as const, name: 'Max' },
            { type: 'min' as const, name: 'Min' },
          ],
          symbol: 'pin',
          symbolSize: 40,
          label: { fontSize: 12 },
        },
      })),
      legend: {
        data: seriesData.map((s) => s.name),
        textStyle: { color: theme?.chart_style?.axis_color ?? '#666' },
      },
    };
  }, [annotationKeyframes, theme, chart_material, props.data]);

  return <ReactECharts option={option} style={{ width: '100%', height: '100%' }} />;
};

export default AnimatedLineChart;
