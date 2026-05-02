// @vitest-environment jsdom

import { describe, it, expect, vi, beforeEach } from "vitest";
import { render } from "@testing-library/react";
import React from "react";

// Spy to verify which template is rendered and with what props
const mockTemplateRender = vi.fn((props: any) =>
  React.createElement("div", { "data-testid": "mock-template" }, JSON.stringify(props.data))
);

vi.mock("../../../../src/frontend/components/templates/template_registry", () => ({
  TEMPLATE_REGISTRY: {
    animated_line_chart: (props: any) => mockTemplateRender(props),
    data_card: (props: any) => mockTemplateRender(props),
  },
}));

import ShotComposition from "../../../../src/frontend/remotion/compositions/ShotComposition";

beforeEach(() => {
  vi.clearAllMocks();
});

describe("ShotComposition", () => {
  const baseProps = {
    shot: {
      shot_id: "shot_01",
      template_type: "animated_line_chart",
      content: { title: "Test Chart", series: [] },
      time_range: { start_seconds: 0, end_seconds: 10 },
    },
    templateType: "animated_line_chart",
    durationInFrames: 300,
    width: 1920,
    height: 1080,
    fps: 30,
  };

  it("renders the template matching template_type from TEMPLATE_REGISTRY", () => {
    render(React.createElement(ShotComposition, baseProps));

    expect(mockTemplateRender).toHaveBeenCalledTimes(1);
    const callProps = mockTemplateRender.mock.calls[0][0];
    expect(callProps.templateId).toBe("animated_line_chart");
    expect(callProps.data).toEqual({ title: "Test Chart", series: [] });
    expect(callProps.fps).toBe(30);
  });

  it("renders fallback when template_type is not in registry", () => {
    const fallbackProps = {
      ...baseProps,
      shot: {
        ...baseProps.shot,
        template_type: "nonexistent_template",
        content: { text: "Fallback content" },
      },
      templateType: "nonexistent_template",
    };

    const { container } = render(
      React.createElement(ShotComposition, fallbackProps)
    );

    expect(mockTemplateRender).not.toHaveBeenCalled();
    expect(container.textContent).toContain("Fallback content");
  });

  it("provides sensible defaults for timeline segment and annotation keyframes", () => {
    render(React.createElement(ShotComposition, baseProps));

    const callProps = mockTemplateRender.mock.calls[0][0];
    expect(callProps.timelineSegment).toEqual({
      startFrame: 0,
      endFrame: 300,
    });
    expect(callProps.annotationKeyframes).toEqual([]);
  });

  it("uses theme from shot content when available", () => {
    const themedProps = {
      ...baseProps,
      shot: {
        ...baseProps.shot,
        content: { title: "Styled", theme: { background_color: "#ff0000" } },
      },
    };

    render(React.createElement(ShotComposition, themedProps));

    const callProps = mockTemplateRender.mock.calls[0][0];
    expect(callProps.theme).toEqual({ background_color: "#ff0000" });
  });
});
