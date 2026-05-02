import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StoryboardEditor } from "@frontend/components/StoryboardEditor";
import { calcSplitDurations } from "@frontend/components/storyboard/ShotSplitter";
import type { ShotCard } from "@frontend/components/StoryboardEditor";

const sampleShots: ShotCard[] = [
  {
    id: "shot-1",
    description: "Opening scene",
    duration_sec: 5.0,
    template_id: "tpl-intro",
    anchor_text: "Hello world",
    anchor_start: 0,
    anchor_end: 11,
    scene_type: "intro",
    claim_count: 1,
    preview_state: "preview",
  },
  {
    id: "shot-2",
    description: "Main content",
    duration_sec: 10.0,
    template_id: "tpl-main",
    anchor_text: "This is the main",
    anchor_start: 13,
    anchor_end: 30,
    scene_type: "main",
    claim_count: 3,
    preview_state: "production",
  },
];

const sampleScript = "Hello world. This is the main content.";

describe("StoryboardEditor", () => {
  it("AC-1 selecting shot highlights anchor_text in script pane", async () => {
    render(
      <StoryboardEditor
        project_id="proj-1"
        shots={sampleShots}
        polished_script={sampleScript}
      />
    );

    // No highlight before selection
    expect(screen.queryByTestId("anchor-highlight")).toBeNull();

    // Click on shot-2 card to select it
    await userEvent.click(screen.getByTestId("shot-card-shot-2"));

    // Highlight should appear with the selected shot's anchor text
    const highlight = screen.getByTestId("anchor-highlight");
    expect(highlight).toBeInTheDocument();
    expect(highlight.textContent).toContain("This is the main");
  });

  it("AC-2 selecting a shot reveals split handle; interacting calls onShotSplit", async () => {
    const onSplit = vi.fn();
    render(
      <StoryboardEditor
        project_id="proj-1"
        shots={sampleShots}
        polished_script={sampleScript}
        onShotSplit={onSplit}
      />
    );

    // No split handle without selection
    expect(screen.queryByTestId("split-handle")).toBeNull();

    // Select shot-1
    await userEvent.click(screen.getByTestId("shot-card-shot-1"));

    // Split handle should now exist
    const handle = screen.getByTestId("split-handle");
    expect(handle).toBeInTheDocument();

    // Trigger split via the handle
    await userEvent.click(handle);

    // onShotSplit must be called with the selected shot's id and a numeric offset
    expect(onSplit).toHaveBeenCalledWith("shot-1", expect.any(Number));
    const offset = onSplit.mock.calls[0][1];
    expect(offset).toBeGreaterThanOrEqual(0);
  });

  it("AC-3 calcSplitDurations returns child durations that sum to parent within 100ms", () => {
    // Parent 10.0s, anchor [0, 20], split at offset 8
    const [leftDur, rightDur] = calcSplitDurations(10.0, 0, 20, 8);

    // 8/20 * 10.0 = 4.0, 12/20 * 10.0 = 6.0
    expect(leftDur).toBeCloseTo(4.0, 2);
    expect(rightDur).toBeCloseTo(6.0, 2);
    expect(leftDur + rightDur).toBeCloseTo(10.0, 1);

    // Midpoint split
    const [l2, r2] = calcSplitDurations(15.0, 10, 30, 20);
    // 10/20 * 15.0 = 7.5, 10/20 * 15.0 = 7.5
    expect(l2).toBeCloseTo(7.5, 2);
    expect(r2).toBeCloseTo(7.5, 2);
    expect(l2 + r2).toBeCloseTo(15.0, 1);
  });

  it("AC-4 shot card renders scene_type duration claim_count preview state", () => {
    render(
      <StoryboardEditor
        project_id="proj-1"
        shots={sampleShots}
        polished_script={sampleScript}
      />
    );

    // Card exists for shot-2
    const card = screen.getByTestId("shot-card-shot-2");
    expect(card).toBeInTheDocument();

    // scene_type badge
    expect(screen.getByTestId("shot-card-shot-2-scene_type")).toHaveTextContent("main");

    // duration formatted as M:SS (10.0 sec -> "0:10")
    expect(screen.getByTestId("shot-card-shot-2-duration")).toHaveTextContent("0:10");

    // claim count badge
    expect(screen.getByTestId("shot-card-shot-2-claim_count")).toHaveTextContent("3");

    // mode chip shows production state
    expect(screen.getByTestId("shot-card-shot-2-mode")).toHaveTextContent("production");
  });
});
