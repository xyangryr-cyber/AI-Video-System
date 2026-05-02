// Root entry point for server-side shot rendering via Node.js.
// Registers the ShotRender composition so @remotion/bundler can find it.
import { registerRoot, Composition } from "remotion";
import type { CalculateMetadataFunction } from "remotion";
import ShotComposition from "./compositions/ShotComposition";
import type { ShotRenderInput } from "@shared/types/shot_render";

const DEFAULT_PROPS: ShotRenderInput = {
  shot: {
    shot_id: "shot_000",
    time_range: { start_seconds: 0, end_seconds: 10 },
    type: "template",
    template_type: "chart_card",
    content: "",
  },
  templateType: "chart_card",
  durationInFrames: 300,
  width: 1920,
  height: 1080,
  fps: 30,
};

const calculateMetadata: CalculateMetadataFunction<ShotRenderInput> = ({
  defaultProps,
  props,
}) => {
  const durationInFrames = props.durationInFrames ?? defaultProps.durationInFrames;
  return {
    durationInFrames: Math.max(1, Math.round(durationInFrames)),
    props,
  };
};

const RootShotRender = () => (
  <Composition
    id="ShotRender"
    component={ShotComposition}
    durationInFrames={DEFAULT_PROPS.durationInFrames}
    fps={DEFAULT_PROPS.fps}
    width={DEFAULT_PROPS.width}
    height={DEFAULT_PROPS.height}
    defaultProps={DEFAULT_PROPS}
    calculateMetadata={calculateMetadata}
  />
);

registerRoot(RootShotRender);
