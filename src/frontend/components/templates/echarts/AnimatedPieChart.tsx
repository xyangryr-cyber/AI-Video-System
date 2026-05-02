import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { TemplateProps } from '@shared/types/template_props';
import {
  resolveChartData,
  validateChartMaterial,
} from '@frontend/render/chart_material_priority';

const AnimatedPieChart: React.FC<TemplateProps> = (props) => {
  const { annotationKeyframes, theme, chart_material } = props;

  const option = useMemo(() => {
    validateChartMaterial(props);
    const resolved = resolveChartData(props);

    const colorPalette = theme?.color_palette ?? [
      '#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE',
    ];

    let pieData: { name: string; value: number }[] = [];
    let pieName = 'Pie';

    if (resolved.source === "chart_material" && Array.isArray(resolved.data)) {
      const seriesArr = resolved.data as { name: string; data: number[] }[];
      // For pie, the first series' data becomes values, names from labels/x_axis
      const firstSeries = seriesArr[0];
      const labels = resolved.axisSpec?.x_axis?.labels as string[] | undefined;
      if (firstSeries) {
        pieName = firstSeries.name || 'Pie';
        pieData = firstSeries.data.map((val, i) => ({
          name: labels?.[i] ?? `Item ${i + 1}`,
          value: val,
        }));
      }
    } else {
      const raw = resolved.data as {
        labels: string[];
        values: number[];
        name?: string;
      } | null;
      if (!raw) return {};
      pieName = raw.name ?? 'Pie';
      pieData = (raw.labels ?? []).map((label, i) => ({
        name: label,
        value: raw.values?.[i] ?? 0,
      }));
    }

    return {
      color: colorPalette,
      backgroundColor: theme?.background_color ?? 'transparent',
      animation: true,
      animationDuration: 1500,
      startAngle: 90,
      tooltip: { trigger: 'item' as const },
      series: [
        {
          name: pieName,
          type: 'pie' as const,
          radius: ['40%', '70%'],
          center: ['50%', '50%'],
          roseType: 'radius' as const,
          selectedMode: 'single' as const,
          startAngle: 90,
          animationDuration: 1500,
          emphasis: {
            label: { fontSize: 20, fontWeight: 'bold' },
            itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.3)' },
          },
          label: {
            show: true,
            fontSize: theme?.chart_style?.label_font_size ?? 12,
          },
          data: pieData,
        },
      ],
      legend: {
        orient: 'vertical' as const,
        left: 'left',
        textStyle: { color: theme?.chart_style?.axis_color ?? '#666' },
      },
    };
  }, [annotationKeyframes, theme, chart_material, props.data]);

  return <ReactECharts option={option} style={{ width: '100%', height: '100%' }} />;
};

export default AnimatedPieChart;
