import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { TemplateProps } from '@shared/types/template_props';

const ComparisonChart: React.FC<TemplateProps> = ({
  data,
  annotationKeyframes,
  theme,
}) => {
  const option = useMemo(() => {
    const raw = data as {
      xAxis: { data: string[] };
      series: { name: string; data: number[]; type: string; markArea?: unknown; markLine?: unknown }[];
      markArea?: {
        data: [{ xAxis: string }, { xAxis: string }][];
      };
      markLine?: {
        data: { yAxis: number; label: string }[];
      };
    } | null;
    if (!raw) return {};

    const colorPalette = theme?.color_palette ?? [
      '#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE',
    ];

    return {
      color: colorPalette,
      backgroundColor: theme?.background_color ?? 'transparent',
      animation: true,
      animationDuration: 1200,
      tooltip: { trigger: 'axis' as const },
      xAxis: {
        type: 'category' as const,
        data: raw.xAxis?.data ?? [],
        axisLine: { lineStyle: { color: theme?.chart_style?.axis_color ?? '#ccc' } },
      },
      yAxis: {
        type: 'value' as const,
        splitLine: { lineStyle: { color: theme?.chart_style?.grid_color ?? '#eee' } },
      },
      series: (raw.series ?? []).map((s, i) => ({
        name: s.name,
        type: s.type as 'line' | 'bar',
        data: s.data,
        smooth: s.type === 'line',
        barMaxWidth: s.type === 'bar' ? 30 : undefined,
        markArea: i === 0 && raw.markArea
          ? {
              silent: true,
              data: raw.markArea.data,
              itemStyle: { color: 'rgba(84, 112, 198, 0.1)' },
            }
          : s.markArea,
        markLine: i === 0 && raw.markLine
          ? {
              silent: true,
              data: raw.markLine.data,
              lineStyle: { type: 'dashed' as const },
              label: { show: true },
            }
          : s.markLine,
      })),
      legend: {
        data: (raw.series ?? []).map((s) => s.name),
        textStyle: { color: theme?.chart_style?.axis_color ?? '#666' },
      },
    };
  }, [data, annotationKeyframes, theme]);

  return <ReactECharts option={option} style={{ width: '100%', height: '100%' }} />;
};

export default ComparisonChart;
