import React, { useEffect, useRef, useMemo } from "react";
import ReactECharts from "echarts-for-react";
import type { TemplateProps } from "@shared/types/template_props";
import type { ContinuousKeyframe, ThemeConfig } from "@shared/types/shared_types";
import { computeFrameState } from "./useEChartsFrame";

interface EChartsFrameControllerProps extends TemplateProps {
  frame: number;
  mode: "preview" | "production";
}

function getDataLength(data: unknown): number {
  const d = data as Record<string, unknown> | null;
  if (!d) return 0;
  if (Array.isArray(d)) return d.length;
  if (Array.isArray(d.series)) {
    const s0 = d.series[0] as Record<string, unknown> | undefined;
    if (s0 && Array.isArray(s0.data)) return s0.data.length;
  }
  if (Array.isArray((d.xAxis as Record<string, unknown> | undefined)?.data))
    return ((d.xAxis as Record<string, unknown>).data as unknown[]).length;
  return 0;
}

function buildBaseOption(
  data: unknown,
  theme: ThemeConfig,
  annotationKeyframes: TemplateProps["annotationKeyframes"],
): Record<string, unknown> {
  const d = data as Record<string, unknown> | null;
  const colors = theme?.color_palette ?? ["#5470C6", "#91CC75", "#FAC858", "#EE6666", "#73C0DE"];

  const xData: string[] =
    ((d?.xAxis as Record<string, unknown>)?.data as string[] | undefined) ?? [];
  const series: unknown[] = (d?.series as unknown[]) ?? [];

  const graphic: unknown[] = [];
  if (annotationKeyframes && annotationKeyframes.length > 0) {
    for (const kf of annotationKeyframes) {
      if (kf.type === "discrete" && kf.annotation) {
        graphic.push({
          type: "text",
          left: "center",
          top: 30,
          style: {
            text: kf.annotation,
            fill: colors[0],
            fontSize: 14,
          },
        });
      }
    }
  }

  return {
    color: colors,
    backgroundColor: theme?.background_color ?? "transparent",
    animation: false, // AC-1: ECharts native animation disabled
    tooltip: { trigger: "axis" as const },
    xAxis: {
      type: "category" as const,
      data: xData,
      axisLine: {
        lineStyle: { color: theme?.chart_style?.axis_color ?? "#ccc" },
      },
    },
    yAxis: {
      type: "value" as const,
      splitLine: {
        lineStyle: { color: theme?.chart_style?.grid_color ?? "#eee" },
      },
    },
    graphic: graphic.length > 0 ? graphic : undefined,
    series: series.map((s, i) => {
      const seriesItem = s as Record<string, unknown>;
      return {
        name: seriesItem.name ?? `Series ${i + 1}`,
        type: (seriesItem.type as string) ?? "line",
        data: seriesItem.data ?? [],
        smooth: true,
        lineStyle: { width: 2 },
      };
    }),
    legend: {
      data: series.map((s, i) => {
        const seriesItem = s as Record<string, unknown>;
        return seriesItem.name ?? `Series ${i + 1}`;
      }),
      textStyle: { color: theme?.chart_style?.axis_color ?? "#666" },
    },
    dataZoom: [
      {
        type: "slider" as const,
        startValue: 0,
        endValue: 0,
        show: false,
      },
    ],
  };
}

const EChartsFrameController: React.FC<EChartsFrameControllerProps> = (props) => {
  const { frame, fps, data, annotationKeyframes, timelineSegment, theme, mode } = props;

  const chartRef = useRef<ReactECharts>(null);

  const durationInFrames = timelineSegment.endFrame - timelineSegment.startFrame;

  const pauseTriggers = useMemo(
    () =>
      annotationKeyframes
        .filter((kf) => kf.type === "continuous")
        .flatMap((kf) => (kf as ContinuousKeyframe).pause_triggers ?? [])
        .map((pt) => ({
          at_progress: pt.at_progress,
          duration_sec: pt.duration_sec,
        })),
    [annotationKeyframes],
  );

  const frameState = useMemo(
    () =>
      computeFrameState({
        frame,
        fps,
        durationInFrames,
        pauseTriggers,
      }),
    [frame, fps, durationInFrames, pauseTriggers],
  );

  // In preview mode, only render frame 0 (static snapshot)
  const effectiveFrame = mode === "preview" ? 0 : frame;

  const baseOption = useMemo(
    () => buildBaseOption(data, theme, annotationKeyframes),
    [data, theme, annotationKeyframes],
  );

  // On each frame, update dataZoom range and enforce animation: false
  useEffect(() => {
    const instance = chartRef.current?.getEchartsInstance();
    if (!instance) return;

    // AC-4: During pause, do not call setOption — ECharts holds current state
    if (frameState.isPaused) return;

    const dataLen = getDataLength(data);
    const endIdx = Math.max(1, Math.floor(frameState.easedProgress * dataLen));

    instance.setOption({
      animation: false,
      dataZoom: [
        {
          type: "slider",
          startValue: 0,
          endValue: endIdx - 1,
          show: false,
        },
      ],
    });
  }, [effectiveFrame, frameState.isPaused, frameState.easedProgress, data]);

  return (
    <ReactECharts
      ref={chartRef}
      option={baseOption}
      style={{ width: "100%", height: "100%" }}
      notMerge={false}
    />
  );
};

export default EChartsFrameController;
