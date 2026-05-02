// [SPEC-F-012] PreviewPlayer — @remotion/player-based preview with keyboard shortcuts,
// playback speed controls, JKL shuttle, M-key annotation, and 4-layer decomposition.

import { useCallback, useState, type FC, type KeyboardEvent } from "react";
import { Player } from "@remotion/player";
import type { TemplateProps } from "@shared/types/template_props";
import { matchKeyboardAction } from "./KeyboardControls";
import TimelineAnnotation from "./TimelineAnnotation";
import type { UserAnnotation } from "./TimelineAnnotation";
import LayerToggle, { type VisibleLayers, type LayerName } from "./LayerToggle";
import VideoComposition from "./VideoComposition";

export interface PreviewPlayerProps {
  /** Shots for the video composition */
  shots: TemplateProps[];
  /** Total duration in frames */
  durationInFrames: number;
  /** Frames per second */
  fps?: number;
}

type PlaybackSpeed = 0.5 | 1 | 1.5 | 2;

/**
 * PreviewPlayer wraps @remotion/player with keyboard controls,
 * layer decomposition, and timeline annotation.
 */
const PreviewPlayer: FC<PreviewPlayerProps> = ({
  shots,
  durationInFrames,
  fps = 30,
}) => {
  const [currentFrame, setCurrentFrame] = useState(0);
  const [playbackSpeed, setPlaybackSpeed] = useState<PlaybackSpeed>(1);
  const [visibleLayers, setVisibleLayers] = useState<VisibleLayers>({
    text: true,
    data: true,
    visual: true,
    audio: true,
  });
  const [annotations, setAnnotations] = useState<UserAnnotation[]>([]);

  const handleToggleLayer = useCallback((layer: LayerName) => {
    setVisibleLayers((prev) => ({
      ...prev,
      [layer]: !prev[layer],
    }));
  }, []);

  const handleAnnotation = useCallback((annotation: UserAnnotation) => {
    setAnnotations((prev) => [...prev, annotation]);
    // In production, this is POSTed to task_ledger via API.
    console.log("task_ledger annotation:", JSON.stringify(annotation));
  }, []);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      const mapping = matchKeyboardAction(e.nativeEvent);

      if (!mapping) return;

      switch (mapping.action) {
        case "step_forward_1":
          e.preventDefault();
          setCurrentFrame((f) => Math.min(f + 1, durationInFrames - 1));
          break;
        case "step_backward_1":
          e.preventDefault();
          setCurrentFrame((f) => Math.max(f - 1, 0));
          break;
        case "step_forward_10":
          e.preventDefault();
          setCurrentFrame((f) => Math.min(f + 10, durationInFrames - 1));
          break;
        case "step_backward_10":
          e.preventDefault();
          setCurrentFrame((f) => Math.max(f - 10, 0));
          break;
        case "speed_0_5x":
          setPlaybackSpeed(0.5);
          break;
        case "speed_1x":
          setPlaybackSpeed(1);
          break;
        case "speed_1_5x":
          setPlaybackSpeed(1.5);
          break;
        case "speed_2x":
          setPlaybackSpeed(2);
          break;
        case "annotate":
          // M-key handled by TimelineAnnotation component
          break;
        case "toggle_play":
          // K/J: handled by @remotion/player internally
          break;
        default:
          break;
      }
    },
    [durationInFrames]
  );

  return (
    <div
      className="preview-player-container"
      style={{ position: "relative", backgroundColor: "#0a0a1a" }}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Layer toggle controls */}
      <div
        style={{
          position: "absolute",
          top: 8,
          left: "50%",
          transform: "translateX(-50%)",
          zIndex: 10,
        }}
      >
        <LayerToggle
          visibleLayers={visibleLayers}
          onToggle={handleToggleLayer}
        />
      </div>

      {/* Speed indicator */}
      <div
        style={{
          position: "absolute",
          top: 8,
          right: 8,
          color: "rgba(255,255,255,0.5)",
          fontSize: 12,
          fontFamily: "monospace",
          zIndex: 10,
        }}
      >
        {playbackSpeed}x
      </div>

      {/* @remotion/player */}
      <Player
        component={VideoComposition}
        inputProps={{ shots, durationInFrames }}
        durationInFrames={durationInFrames}
        fps={fps}
        compositionWidth={1920}
        compositionHeight={1080}
        playbackRate={playbackSpeed}
        controls
        style={{ width: "100%" }}
      />

      {/* Timeline annotation overlay */}
      <TimelineAnnotation
        currentFrame={currentFrame}
        fps={fps}
        onAnnotation={handleAnnotation}
      />

      {/* Annotation count */}
      {annotations.length > 0 && (
        <div
          style={{
            position: "absolute",
            bottom: 4,
            right: 4,
            color: "rgba(255,255,255,0.3)",
            fontSize: 10,
            fontFamily: "monospace",
          }}
        >
          {annotations.length} annotation(s)
        </div>
      )}
    </div>
  );
};

export default PreviewPlayer;
