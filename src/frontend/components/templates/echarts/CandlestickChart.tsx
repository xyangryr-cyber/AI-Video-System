import React, { useMemo } from 'react';
import ReactECharts from 'echarts-for-react';
import type { TemplateProps } from '@shared/types/template_props';
import {
  resolveChartData,
  validateChartMaterial,
} from '@frontend/render/chart_material_priority';

const CandlestickChart: React.FC<TemplateProps> = (props) => {
  const { annotationKeyframes, theme, chart_material } = props;

  const option = useMemo(() => {
    validateChartMaterial(props);
    const resolved = resolveChartData(props);

    const colorPalette = theme?.color_palette ?? [
      '#EE6666', '#91CC75', '#5470C6', '#FAC858', '#73C0DE',
    ];

    const axisSpec = resolved.axisSpec;

    let dates: string[] = [];
    let ohlc: [number, number, number, number][] = [];
    let volumes: number[][] = [];
    let ma5: number[] | undefined;
    let ma10: number[] | undefined;
    let ma20: number[] | undefined;

    if (resolved.source === "chart_material" && Array.isArray(resolved.data)) {
      const seriesArr = resolved.data as {
        name: string;
        data: (number | [number, number, number, number] | number[])[];
      }[];
      for (const s of seriesArr) {
        if (s.name === 'K-line' || s.name === 'ohlc') {
          ohlc = s.data as [number, number, number, number][];
        } else if (s.name === 'Volume') {
          volumes = (s.data as number[]).map((v, i) => [i, v]);
        } else if (s.name === 'MA5') {
          ma5 = s.data as number[];
        } else if (s.name === 'MA10') {
          ma10 = s.data as number[];
        } else if (s.name === 'MA20') {
          ma20 = s.data as number[];
        }
      }
      if (axisSpec) {
        dates = (axisSpec.x_axis.labels ?? []) as string[];
      }
    } else {
      const raw = resolved.data as {
        dates: string[];
        ohlc: [number, number, number, number][];
        volumes: number[][];
        ma5?: number[];
        ma10?: number[];
        ma20?: number[];
      } | null;
      if (!raw) return {};
      dates = raw.dates ?? [];
      ohlc = raw.ohlc ?? [];
      volumes = raw.volumes ?? [];
      ma5 = raw.ma5;
      ma10 = raw.ma10;
      ma20 = raw.ma20;
    }

    return {
      color: colorPalette,
      backgroundColor: theme?.background_color ?? 'transparent',
      animation: true,
      animationDelay(idx: number) {
        return idx * 30;
      },
      tooltip: {
        trigger: 'axis' as const,
        axisPointer: { type: 'cross' as const },
      },
      grid: [
        { left: '10%', right: '8%', top: '20%', height: '50%' },
        { left: '10%', right: '8%', top: '75%', height: '15%' },
      ],
      xAxis: [
        {
          type: 'category' as const,
          data: dates,
          gridIndex: 0,
          axisLine: { lineStyle: { color: theme?.chart_style?.axis_color ?? '#ccc' } },
        },
        {
          type: 'category' as const,
          data: dates,
          gridIndex: 1,
          axisLine: { lineStyle: { color: theme?.chart_style?.axis_color ?? '#ccc' } },
          axisLabel: { show: false },
        },
      ],
      yAxis: [
        {
          type: 'value' as const,
          gridIndex: 0,
          scale: true,
          ...(axisSpec?.y_axis?.min !== undefined ? { min: axisSpec.y_axis.min } : {}),
          ...(axisSpec?.y_axis?.max !== undefined ? { max: axisSpec.y_axis.max } : {}),
          splitLine: { lineStyle: { color: theme?.chart_style?.grid_color ?? '#eee' } },
        },
        {
          type: 'value' as const,
          gridIndex: 1,
          splitLine: { show: false },
        },
      ],
      dataZoom: [
        { type: 'inside' as const, xAxisIndex: [0, 1], start: 0, end: 100 },
        { type: 'slider' as const, xAxisIndex: [0, 1], start: 0, end: 100, top: '95%' },
      ],
      series: [
        {
          name: 'K-line',
          type: 'candlestick' as const,
          xAxisIndex: 0,
          yAxisIndex: 0,
          data: ohlc,
          itemStyle: {
            color: colorPalette[1],
            color0: colorPalette[0],
            borderColor: colorPalette[1],
            borderColor0: colorPalette[0],
          },
        },
        ...(ma5
          ? [
              {
                name: 'MA5',
                type: 'line' as const,
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: ma5,
                smooth: true,
                lineStyle: { width: 1 },
                symbol: 'none' as const,
              },
            ]
          : []),
        ...(ma10
          ? [
              {
                name: 'MA10',
                type: 'line' as const,
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: ma10,
                smooth: true,
                lineStyle: { width: 1 },
                symbol: 'none' as const,
              },
            ]
          : []),
        ...(ma20
          ? [
              {
                name: 'MA20',
                type: 'line' as const,
                xAxisIndex: 0,
                yAxisIndex: 0,
                data: ma20,
                smooth: true,
                lineStyle: { width: 1 },
                symbol: 'none' as const,
              },
            ]
          : []),
        {
          name: 'Volume',
          type: 'bar' as const,
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: (volumes ?? []).map(([_, vol]) => vol),
        },
      ],
      legend: {
        data: ['K-line', 'MA5', 'MA10', 'MA20', 'Volume'].filter((n) =>
          n === 'K-line' || n === 'Volume' || (
            n === 'MA5' ? ma5 :
            n === 'MA10' ? ma10 :
            n === 'MA20' ? ma20 :
            false
          )
        ),
        textStyle: { color: theme?.chart_style?.axis_color ?? '#666' },
      },
    };
  }, [annotationKeyframes, theme, chart_material, props.data]);

  return <ReactECharts option={option} style={{ width: '100%', height: '100%' }} />;
};

export default CandlestickChart;
