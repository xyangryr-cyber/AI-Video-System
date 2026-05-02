/**
 * [SPEC-GAPFIX-033] PreviewComposition — Remotion video preview.
 *
 * Uses Remotion <Composition> to render a timeline-based visual preview
 * of the project's video segments. Accepts projectId, timeline, and
 * segments as props.
 */
import type { FC } from "react";
import { Composition } from "remotion";

export interface TimelineSegment {
  id: string;
  start_sec: number;
  end_sec: number;
  phase: number;
}

export interface SegmentInfo {
  id: string;
  title: string;
  duration_sec: number;
}

export interface PreviewCompositionProps {
  projectId: string;
  timeline: {
    total_duration_sec: number;
    segments: TimelineSegment[];
  };
  segments: SegmentInfo[];
}

const SEGMENT_COLORS = [
  "#4A90D9",
  "#7B68EE",
  "#50C878",
  "#FF6B6B",
  "#FFD93D",
  "#6BCB77",
  "#4D96FF",
  "#FF8C00",
  "#9370DB",
];

function segmentColor(index: number): string {
  return SEGMENT_COLORS[index % SEGMENT_COLORS.length];
}

const SegmentTimeline: FC<PreviewCompositionProps> = ({ projectId, timeline, segments }) => {
  const { total_duration_sec } = timeline;

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        backgroundColor: "#1a1a2e",
        color: "#eee",
        fontFamily: "system-ui, sans-serif",
        padding: 24,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
      }}
    >
      <div style={{ marginBottom: 16 }}>
        <h2 style={{ margin: 0, fontSize: 20 }}>Preview — {projectId}</h2>
        <p style={{ margin: "4px 0 0", fontSize: 13, color: "#888" }}>
          Total: {total_duration_sec}s | Segments: {segments.length}
        </p>
      </div>

      <div
        style={{
          flex: 1,
          display: "flex",
          gap: 4,
          alignItems: "stretch",
        }}
      >
        {segments.map((seg, i) => {
          const widthPct = (seg.duration_sec / total_duration_sec) * 100;
          return (
            <div
              key={seg.id}
              style={{
                width: `${widthPct}%`,
                backgroundColor: segmentColor(i),
                borderRadius: 6,
                display: "flex",
                flexDirection: "column",
                justifyContent: "center",
                alignItems: "center",
                padding: 8,
                boxSizing: "border-box",
                minWidth: 0,
              }}
            >
              <span
                style={{
                  fontSize: 13,
                  fontWeight: 600,
                  whiteSpace: "nowrap",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  maxWidth: "100%",
                }}
              >
                {seg.title}
              </span>
              <span style={{ fontSize: 11, opacity: 0.8 }}>{seg.duration_sec}s</span>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const PreviewComposition: FC<PreviewCompositionProps> = (props) => {
  return (
    <Composition
      id="preview-composition"
      component={SegmentTimeline as unknown as FC<Record<string, unknown>>}
      durationInFrames={Math.max(1, props.timeline.total_duration_sec)}
      fps={1}
      width={854}
      height={480}
      defaultProps={props}
    />
  );
};

export default PreviewComposition;
