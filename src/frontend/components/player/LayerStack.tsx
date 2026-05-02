// [SPEC-F-007] LayerStack -- layer stacking via <AbsoluteFill>.
// Layer 3 orchestration: background / chart / annotation / subtitle layers.
// Zero animation imports — only remotion and react.

import type { FC, ReactNode } from "react";
import { AbsoluteFill } from "remotion";
import type { TemplateProps } from "@shared/types/template_props";

export interface LayerStackProps {
  shot: TemplateProps;
  frame: number;
  progress: number;
  paused: boolean;
  children?: ReactNode;
}

/**
 * LayerStack renders the visual layers for a single shot.
 * Layers: background -> content (chart/info) -> annotation -> subtitle overlay.
 */
const LayerStack: FC<LayerStackProps> = ({ shot, frame, progress, paused, children }) => {
  const bgColor = shot.theme.chart_style?.background_color ?? "#1a1a2e";

  return (
    <AbsoluteFill style={{ position: "relative", overflow: "hidden" }}>
      {/* Layer 0: Background */}
      <AbsoluteFill
        style={{
          backgroundColor: bgColor,
          zIndex: 0,
        }}
      />

      {/* Layer 1: Chart / Info content */}
      <AbsoluteFill
        style={{
          zIndex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        {paused ? <div className="pause-indicator" data-paused="true" /> : null}
        {children}
      </AbsoluteFill>

      {/* Layer 2: Annotation overlay (frame counter, watermarks) */}
      <AbsoluteFill
        style={{
          zIndex: 2,
          pointerEvents: "none",
        }}
      >
        <span
          className="frame-counter"
          style={{
            position: "absolute",
            bottom: 8,
            right: 8,
            color: "rgba(255,255,255,0.3)",
            fontSize: 10,
            fontFamily: "monospace",
          }}
        >
          {frame}
        </span>
      </AbsoluteFill>

      {/* Layer 3: Subtitle overlay — reserved for SubtitleRenderer */}
      <AbsoluteFill
        style={{
          zIndex: 3,
          pointerEvents: "none",
        }}
      />
    </AbsoluteFill>
  );
};

export default LayerStack;
