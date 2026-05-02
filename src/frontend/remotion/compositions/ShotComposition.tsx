// ShotComposition — single-shot Remotion composition for server-side rendering.
// Receives ShotRenderInput via inputProps, selects template from TEMPLATE_REGISTRY,
// and renders it with TemplateProps-compatible props.
import type { FC } from "react";
import { useCurrentFrame, useVideoConfig } from "remotion";
import type { TemplateProps } from "@shared/types/template_props";
import type { ShotRenderInput } from "@shared/types/shot_render";
import { TEMPLATE_REGISTRY } from "../../components/templates/template_registry";

const FallbackCard: FC<{ text: string }> = ({ text }) => (
  <div
    style={{
      width: "100%",
      height: "100%",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#0a1628",
      color: "#e0e0e0",
      fontFamily: "sans-serif",
      fontSize: 32,
      padding: 40,
      textAlign: "center",
    }}
  >
    {text || "No content"}
  </div>
);

const ShotComposition: FC<ShotRenderInput> = (props) => {
  const { shot, durationInFrames, width, height, fps } = props;
  const frame = useCurrentFrame();

  const TemplateComponent = TEMPLATE_REGISTRY[shot.template_type];

  if (!TemplateComponent) {
    const fallbackText =
      typeof shot.content === "object" && shot.content !== null
        ? String((shot.content as Record<string, unknown>).text ?? shot.content)
        : String(shot.content ?? "");
    return <FallbackCard text={fallbackText} />;
  }

  const contentObj =
    typeof shot.content === "object" && shot.content !== null
      ? (shot.content as Record<string, unknown>)
      : {};

  const templateProps: TemplateProps = {
    templateId: shot.template_type,
    data: shot.content,
    annotationKeyframes: [],
    timelineSegment: {
      startFrame: 0,
      endFrame: durationInFrames,
    },
    theme: (contentObj.theme as TemplateProps["theme"]) ?? {},
    fps,
  };

  return (
    <div
      style={{
        width,
        height,
        overflow: "hidden",
        position: "relative",
        background: "#0a1628",
      }}
    >
      <TemplateComponent {...templateProps} />
    </div>
  );
};

export default ShotComposition;
