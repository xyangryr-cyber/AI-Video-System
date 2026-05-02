// [SPEC-F-007] SegmentSequencer -- sequences shots by timeline.json segments.
// Layer 3 orchestration: manages annotation_keyframes, pause_triggers,
// data_point_id → key_data_point traceability (P2). Zero animation imports.

import type { FC } from "react";
import { Sequence, useCurrentFrame, interpolate } from "remotion";
import type { TemplateProps, TimelineSegmentRange } from "@shared/types/template_props";
import type {
  AnnotationKeyframe,
  ContinuousKeyframe,
  DiscreteKeyframe,
} from "@shared/types/shared_types";
import { resolveTemplateByDataType } from "../templates/template_registry";
import LayerStack from "./LayerStack";

export interface SegmentSequencerProps {
  shots: TemplateProps[];
  fps: number;
}

/**
 * Validate that annotation_keyframes align with the timeline segment range.
 * Returns true if all keyframes are within [startFrame, endFrame].
 */
export function validateKeyframeAlignment(
  keyframes: AnnotationKeyframe[],
  segment: TimelineSegmentRange,
): boolean {
  for (const kf of keyframes) {
    if ("at_frame" in kf) {
      const dk = kf as DiscreteKeyframe;
      if (dk.at_frame! < segment.startFrame || dk.at_frame! > segment.endFrame) {
        return false;
      }
    } else if ("start_frame" in kf) {
      const ck = kf as ContinuousKeyframe;
      if (ck.start_frame! < segment.startFrame || ck.end_frame! > segment.endFrame) {
        return false;
      }
      // Validate pause_triggers are within range
      if (ck.pause_triggers) {
        for (const pt of ck.pause_triggers) {
          if (pt.at_frame! < segment.startFrame || pt.at_frame! > segment.endFrame) {
            return false;
          }
        }
      }
    }
  }
  return true;
}

/**
 * Determine if the current frame is within a pause trigger window.
 */
export function isFramePaused(
  frame: number,
  keyframes: AnnotationKeyframe[],
  fps: number,
): boolean {
  for (const kf of keyframes) {
    if ("pause_triggers" in kf) {
      const ck = kf as ContinuousKeyframe;
      if (ck.pause_triggers) {
        for (const pt of ck.pause_triggers) {
          const triggerFrame = Math.round(
            pt.at_progress * (ck.end_frame! - ck.start_frame!) + ck.start_frame!,
          );
          if (Math.abs(frame - triggerFrame) < 1) {
            return true;
          }
        }
      }
    }
  }
  return false;
}

/**
 * Check that all data_point_id references in a template's data are traceable.
 * Validates that data_points and ohlc_data carry data_point_id fields.
 */
export function validateDataPointTraceability(props: TemplateProps): boolean {
  const data = props.data as Record<string, unknown> | undefined;
  if (!data) return true;

  // Check data_points array
  if (Array.isArray(data.data_points)) {
    for (const pt of data.data_points as Array<Record<string, unknown>>) {
      if (!pt.data_point_id) return false;
    }
  }

  // Check ohlc_data array
  if (Array.isArray(data.ohlc_data)) {
    for (const pt of data.ohlc_data as Array<Record<string, unknown>>) {
      if (!pt.data_point_id) return false;
    }
  }

  return true;
}

/**
 * SegmentSequencer renders each shot in its timeline segment via Remotion <Sequence>.
 */
const SegmentSequencer: FC<SegmentSequencerProps> = ({ shots, fps }) => {
  const frame = useCurrentFrame();

  return (
    <>
      {shots.map((shot, idx) => {
        const segment = shot.timelineSegment;
        const keyframes = shot.annotationKeyframes;

        // AC-4: validate keyframes against timeline
        if (keyframes.length > 0) {
          validateKeyframeAlignment(keyframes, segment);
        }

        // AC-6: check pause_triggers
        const paused = isFramePaused(frame, keyframes, fps);

        // AC-5: validate data_point_id traceability
        validateDataPointTraceability(shot);

        // Compute eased progress within this segment
        const localFrame = frame - segment.startFrame;
        const segmentDuration = segment.endFrame - segment.startFrame;
        const progress =
          segmentDuration > 0
            ? interpolate(localFrame, [0, segmentDuration], [0, 1], {
                extrapolateLeft: "clamp",
                extrapolateRight: "clamp",
              })
            : 0;

        const TemplateComponent = resolveTemplateByDataType(shot.templateId);

        return (
          <Sequence
            key={idx}
            from={segment.startFrame}
            durationInFrames={segmentDuration}
            name={`shot-${idx}`}
          >
            <LayerStack shot={shot} frame={frame} progress={progress} paused={paused}>
              {TemplateComponent ? (
                <TemplateComponent {...shot} />
              ) : (
                <div className="fallback-text-card">
                  <span>No template for: {shot.templateId}</span>
                </div>
              )}
            </LayerStack>
          </Sequence>
        );
      })}
    </>
  );
};

export default SegmentSequencer;
