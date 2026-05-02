/**
 * [SPEC-GAPFIX-033] Tests for PreviewComposition component.
 *
 * Verifies:
 * - File exists and exports a Remotion Composition
 * - Accepts projectId, timeline, segments props
 * - Renders timeline segments visual preview
 */
import { describe, it, expect } from "vitest";
import { render } from "@testing-library/react";
import PreviewComposition from "@frontend/remotion/PreviewComposition";

const MOCK_TIMELINE = {
  total_duration_sec: 60,
  segments: [
    { id: "seg_1", start_sec: 0, end_sec: 15, phase: 4 },
    { id: "seg_2", start_sec: 15, end_sec: 40, phase: 5 },
    { id: "seg_3", start_sec: 40, end_sec: 60, phase: 6 },
  ],
};

const MOCK_SEGMENTS = [
  { id: "seg_1", title: "Introduction", duration_sec: 15 },
  { id: "seg_2", title: "Data Analysis", duration_sec: 25 },
  { id: "seg_3", title: "Conclusion", duration_sec: 20 },
];

describe("PreviewComposition", () => {
  it("renders without crashing", () => {
    const { container } = render(
      <PreviewComposition
        projectId="proj_test_033"
        timeline={MOCK_TIMELINE}
        segments={MOCK_SEGMENTS}
      />
    );
    expect(container).toBeTruthy();
  });

  it("renders all timeline segments", () => {
    const { getByText } = render(
      <PreviewComposition
        projectId="proj_test_033"
        timeline={MOCK_TIMELINE}
        segments={MOCK_SEGMENTS}
      />
    );
    expect(getByText("Introduction")).toBeTruthy();
    expect(getByText("Data Analysis")).toBeTruthy();
    expect(getByText("Conclusion")).toBeTruthy();
  });

  it("displays project ID", () => {
    const { getByText } = render(
      <PreviewComposition
        projectId="proj_test_033"
        timeline={MOCK_TIMELINE}
        segments={MOCK_SEGMENTS}
      />
    );
    expect(getByText(/proj_test_033/)).toBeTruthy();
  });

  it("renders segment durations", () => {
    const { getByText } = render(
      <PreviewComposition
        projectId="proj_test_033"
        timeline={MOCK_TIMELINE}
        segments={MOCK_SEGMENTS}
      />
    );
    expect(getByText(/15/)).toBeTruthy();
    expect(getByText(/25/)).toBeTruthy();
    expect(getByText(/20/)).toBeTruthy();
  });
});
