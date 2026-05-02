import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { TemplateProps } from '@shared/types/template_props';
import {
  resolveChartData,
  validateChartMaterial,
} from '@frontend/render/chart_material_priority';

const AnimatedBarChart: React.FC<TemplateProps> = (props) => {
  const { annotationKeyframes, theme, chart_material } = props;

  const option = useMemo(() => {
    validateChartMaterial(props);
    const resolved = resolveChartData(props);

    const colorPalette = theme?.color_palette ?? [
      '#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE',
    ];

    const axisSpec = resolved.axisSpec;
    const resolvedData = resolved.data;

    let xData: string[] = [];
    let seriesData: { name: string; data: number[]; type: string }[] = [];

    if (resolved.source === "chart_material" && Array.isArray(resolvedData)) {
      seriesData = (resolvedData as { name: string; data: number[] }[]).map(
        (s) => ({ ...s, type: "bar" as const }),
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
        type: 'bar' as const,
        data: s.data,
      }));
    }

    const yAxisMin = axisSpec?.y_axis?.min;
    const yAxisMax = axisSpec?.y_axis?.max;

    return {
      color: colorPalette,
      backgroundColor: theme?.background_color ?? 'transparent',
      animation: true,
      animationDuration: 1000,
      animationDelay(dataIndex: number) {
        return dataIndex * 100;
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
      series: seriesData.map((s, _i) => ({
        name: s.name,
        type: 'bar' as const,
        data: s.data,
        barMaxWidth: 40,
        emphasis: {
          itemStyle: {
            color: '#FF6B6B',
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.3)',
          },
        },
        itemStyle: {
          borderRadius: [4, 4, 0, 0],
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

export default AnimatedBarChart;
