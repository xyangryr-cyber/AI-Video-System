import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { TemplateProps } from '@shared/types/template_props';

const TreemapChart: React.FC<TemplateProps> = ({
  data,
  annotationKeyframes,
  theme,
}) => {
  const option = useMemo(() => {
    const raw = data as {
      name: string;
      children: { name: string; value: number; children?: { name: string; value: number }[] }[];
    } | null;
    if (!raw) return {};

    const colorPalette = theme?.color_palette ?? [
      '#5470C6', '#91CC75', '#FAC858', '#EE6666', '#73C0DE',
    ];

    return {
      color: colorPalette,
      backgroundColor: theme?.background_color ?? 'transparent',
      animation: true,
      animationDurationUpdate: 800,
      tooltip: {
        formatter(params: { name: string; value: number; treePathInfo?: { name: string }[] }) {
          const path = (params.treePathInfo ?? [])
            .map((n) => n.name)
            .join(' > ');
          return `${path}<br/>${params.name}: ${params.value}`;
        },
      },
      series: [
        {
          name: raw.name ?? 'Treemap',
          type: 'treemap' as const,
          visibleMin: 300,
          label: {
            show: true,
            formatter(params: { name: string }) {
              return params.name;
            },
          },
          upperLabel: {
            show: true,
            height: 30,
            fontSize: theme?.chart_style?.label_font_size ?? 12,
          },
          itemStyle: {
            borderColor: theme?.background_color ?? '#fff',
            borderWidth: 2,
          },
          roam: false,
          drillDownEnabled: true,
          levels: [
            {
              itemStyle: {
                borderWidth: 2,
                gapWidth: 2,
              },
            },
            {
              colorSaturation: [0.35, 0.5],
              itemStyle: {
                borderColorSaturation: 0.6,
                gapWidth: 1,
              },
            },
          ],
          data: raw.children ?? [],
        },
      ],
    };
  }, [data, annotationKeyframes, theme]);

  return <ReactECharts option={option} style={{ width: '100%', height: '100%' }} />;
};

export default TreemapChart;
