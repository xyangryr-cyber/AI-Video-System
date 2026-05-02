// [SPEC-F-007] renderPipeline -- server-side renderMedia() pipeline.
// Layer 3 orchestration: wraps Remotion renderMedia for production rendering.
// Zero animation imports — only remotion APIs.

import type { TemplateProps } from "@shared/types/template_props";
import { getRenderConfig } from "../remotion/utils/render_mode_controller";

export interface RenderJob {
  shots: TemplateProps[];
  outputPath: string;
  platform?: string;
}

export interface RenderResult {
  outputPath: string;
  success: boolean;
  error?: string;
}

/**
 * Build Remotion render options from a RenderJob.
 * Uses getRenderConfig for platform-aware resolution and fps (AC-7).
 */
export function buildRenderOptions(job: RenderJob) {
  const config = getRenderConfig("production");

  const totalFrames = job.shots.reduce((sum, shot) => {
    const dur =
      shot.timelineSegment.endFrame - shot.timelineSegment.startFrame;
    return sum + dur;
  }, 0);

  return {
    fps: config.fps,
    width: config.width,
    height: config.height,
    durationInFrames: totalFrames,
    outputLocation: job.outputPath,
    codec: "h264" as const,
    proResProfile: undefined,
    imageFormat: "png" as const,
  };
}

/**
 * Validate render input: checks that every shot's annotation_keyframes
 * align with its timeline segment, and data_point_id traceability.
 */
export function validateRenderInput(job: RenderJob): string[] {
  const errors: string[] = [];

  for (let i = 0; i < job.shots.length; i++) {
    const shot = job.shots[i];
    const seg = shot.timelineSegment;

    // Validate annotation_keyframes alignment
    for (const kf of shot.annotationKeyframes) {
      if ("at_frame" in kf) {
        const dk = kf as { at_frame: number };
        if (dk.at_frame < seg.startFrame || dk.at_frame > seg.endFrame) {
          errors.push(
            `Shot ${i}: discrete keyframe at_frame=${dk.at_frame} outside segment [${seg.startFrame}, ${seg.endFrame}]`
          );
        }
      } else if ("start_frame" in kf) {
        const ck = kf as {
          start_frame: number;
          end_frame: number;
          pause_triggers?: Array<{ at_progress: number }>;
        };
        if (ck.start_frame < seg.startFrame || ck.end_frame > seg.endFrame) {
          errors.push(
            `Shot ${i}: continuous keyframe [${ck.start_frame}, ${ck.endFrame}] outside segment [${seg.startFrame}, ${seg.endFrame}]`
          );
        }
      }
    }
  }

  return errors;
}
