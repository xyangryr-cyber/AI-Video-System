import React, { useEffect, useMemo, useState } from "react";
import ReactECharts from "echarts-for-react";
import type { TemplateProps } from "@shared/types/template_props";

const NumberCallout: React.FC<TemplateProps> = ({ data, annotationKeyframes, theme }) => {
  const raw = useMemo(() => {
    return data as {
      number: number;
      unit?: string;
      count_up_duration: number;
      emphasis_color?: string;
      comparison?: {
        label: string;
        value: number;
        delta: number;
        delta_unit: string;
      };
    } | null;
  }, [data]);

  const targetNumber = raw?.number ?? 0;
  const countUpDuration = raw?.count_up_duration ?? 2000;
  const emphasisColor = raw?.emphasis_color ?? "#FF6B6B";
  const unit = raw?.unit ?? "";
  const comparison = raw?.comparison;

  const [displayNumber, setDisplayNumber] = useState(0);

  useEffect(() => {
    if (targetNumber === 0) {
      setDisplayNumber(0);
      return;
    }
    const startTime = Date.now();
    const timer = setInterval(() => {
      const elapsed = Date.now() - startTime;
      const progress = Math.min(elapsed / countUpDuration, 1);
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayNumber(Math.round(targetNumber * eased));
      if (progress >= 1) {
        clearInterval(timer);
      }
    }, 16);
    return () => clearInterval(timer);
  }, [targetNumber, countUpDuration]);

  // CSS @keyframes for pulse-scale effect is injected once
  useEffect(() => {
    const styleId = "number-callout-pulse";
    if (document.getElementById(styleId)) return;
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = `
      @keyframes numberCalloutPulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.08); }
        100% { transform: scale(1); }
      }
    `;
    document.head.appendChild(style);
    return () => {
      const el = document.getElementById(styleId);
      if (el) el.remove();
    };
  }, []);

  const option = useMemo(() => {
    if (!raw) return {};

    return {
      backgroundColor: theme?.background_color ?? "transparent",
      graphic: [
        // Main number with count-up value
        {
          type: "text" as const,
          left: "center",
          top: "30%",
          style: {
            text: `${displayNumber.toLocaleString()}${unit}`,
            font: `bold 48px ${theme?.font_family ?? "Arial"}`,
            fill: emphasisColor,
          },
        },
        // Unit label
        {
          type: "text" as const,
          left: "center",
          top: "50%",
          style: {
            text: comparison
              ? `vs ${comparison.label}: ${comparison.value}${comparison.delta_unit}`
              : "",
            font: `14px ${theme?.font_family ?? "Arial"}`,
            fill: theme?.chart_style?.axis_color ?? "#999",
          },
        },
        // Delta
        {
          type: "text" as const,
          left: "center",
          top: "60%",
          style: {
            text:
              comparison && comparison.delta !== 0
                ? `${comparison.delta > 0 ? "+" : ""}${comparison.delta}${comparison.delta_unit}`
                : "",
            font: `bold 20px ${theme?.font_family ?? "Arial"}`,
            fill: comparison ? (comparison.delta >= 0 ? "#91CC75" : "#EE6666") : "#999",
          },
        },
      ],
      // Annotations from keyframes
      ...(annotationKeyframes && annotationKeyframes.length > 0
        ? {
            graphic: [
              ...annotationKeyframes
                .filter((kf) => kf.type === "discrete")
                .map((kf) => ({
                  type: "text" as const,
                  left: "center",
                  top: "75%",
                  style: {
                    text: (kf as { annotation?: string }).annotation ?? "",
                    font: `12px ${theme?.font_family ?? "Arial"}`,
                    fill: emphasisColor,
                  },
                })),
            ],
          }
        : {}),
    };
  }, [displayNumber, raw, comparison, emphasisColor, unit, theme, annotationKeyframes]);

  return (
    <div style={{ position: "relative", width: "100%", height: "100%" }}>
      <ReactECharts option={option} style={{ width: "100%", height: "100%" }} />
      <div
        style={{
          position: "absolute",
          top: "30%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          animation: "numberCalloutPulse 2s ease-in-out infinite",
          pointerEvents: "none",
        }}
      >
        <span
          style={{
            fontSize: 48,
            fontWeight: "bold",
            color: emphasisColor,
            fontFamily: theme?.font_family ?? "Arial",
          }}
        >
          {displayNumber.toLocaleString()}
          {unit}
        </span>
      </div>
      {comparison && (
        <div
          style={{
            position: "absolute",
            bottom: "20%",
            left: "50%",
            transform: "translateX(-50%)",
            fontSize: 14,
            color: theme?.chart_style?.axis_color ?? "#999",
            fontFamily: theme?.font_family ?? "Arial",
          }}
        >
          vs {comparison.label}: {comparison.value}
          {comparison.delta_unit}
          <span style={{ marginLeft: 8, color: comparison.delta >= 0 ? "#91CC75" : "#EE6666" }}>
            {comparison.delta > 0 ? "+" : ""}
            {comparison.delta}
            {comparison.delta_unit}
          </span>
        </div>
      )}
    </div>
  );
};

export default NumberCallout;
