// [SPEC-F-007] VideoComposition -- Remotion <Composition> definition.
// Layer 3 orchestration: reads fps/width/height from platform profile config.
// Zero animation library imports — only remotion and react are used.

import type { FC } from "react";
import { Composition } from "remotion";
import type { TemplateProps } from "@shared/types/template_props";
import { getRenderConfig } from "../../remotion/utils/render_mode_controller";
import SegmentSequencer from "./SegmentSequencer";

export interface VideoCompositionProps {
  /** All shots for this video, each carrying TemplateProps-compatible data */
  shots: TemplateProps[];
  /** Total duration in frames for the composition */
  durationInFrames: number;
  /** Platform key (e.g. "youtube_16_9") */
  platform?: string;
}

/**
 * VideoComposition defines the full video composition.
 *
 * Uses getRenderConfig for fps/width/height (AC-7: platform profile config).
 * Orchestrates SegmentSequencer for each shot's timeline segment.
 */
const VideoComposition: FC<VideoCompositionProps> = ({
  shots,
  durationInFrames,
  platform = "youtube_16_9",
}) => {
  const config = getRenderConfig("production");
  const fps = config.fps;
  const width = config.width;
  const height = config.height;

  return (
    <Composition
      id="VideoComposition"
      component={() => <SegmentSequencer shots={shots} fps={fps} />}
      fps={fps}
      width={width}
      height={height}
      durationInFrames={durationInFrames}
    />
  );
};

export default VideoComposition;
