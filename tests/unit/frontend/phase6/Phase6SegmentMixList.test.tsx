import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Phase6SegmentMixList } from "@frontend/components/phase6/Phase6SegmentMixList";

const mockAudio = { play: vi.fn().mockResolvedValue(undefined), pause: vi.fn(), load: vi.fn() };
window.HTMLMediaElement.prototype.play = mockAudio.play;
window.HTMLMediaElement.prototype.pause = mockAudio.pause;
window.HTMLMediaElement.prototype.load = mockAudio.load;

interface SegmentEntry {
  id: string;
  index: number;
  preview_url: string;
  text: string;
}

const segments: SegmentEntry[] = [
  { id: "seg_1", index: 1, preview_url: "/media/seg1.mp3", text: "片段一" },
  { id: "seg_2", index: 2, preview_url: "/media/seg2.mp3", text: "片段二" },
];

describe("Phase6SegmentMixList", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-2: disabled until confirm layout", () => {
    it("shows cursor not-allowed when not confirmed", () => {
      render(
        <Phase6SegmentMixList
          segments={segments}
          confirmed={false}
          onMixFeedback={vi.fn()}
        />,
      );
      const list = screen.getByTestId("segment-mix-list");
      expect(list.className).toContain("cursor-not-allowed");
    });

    it("has aria-disabled when not confirmed", () => {
      render(
        <Phase6SegmentMixList
          segments={segments}
          confirmed={false}
          onMixFeedback={vi.fn()}
        />,
      );
      const list = screen.getByTestId("segment-mix-list");
      expect(list).toHaveAttribute("aria-disabled", "true");
    });

    it("prevents feedback submission when disabled", () => {
      render(
        <Phase6SegmentMixList
          segments={segments}
          confirmed={false}
          onMixFeedback={vi.fn()}
        />,
      );
      const buttons = screen.queryAllByRole("button", { name: /提交反馈|submit feedback/i });
      buttons.forEach((b) => expect(b).toBeDisabled());
    });

    it("enables interaction when confirmed", () => {
      render(
        <Phase6SegmentMixList
          segments={segments}
          confirmed={true}
          onMixFeedback={vi.fn()}
        />,
      );
      const list = screen.getByTestId("segment-mix-list");
      expect(list).not.toHaveAttribute("aria-disabled", "true");
    });
  });

  describe("AC-3: mix_feedback refreshes segment preview", () => {
    it("calls onMixFeedback with segment id", () => {
      const onFeedback = vi.fn();
      render(
        <Phase6SegmentMixList
          segments={segments}
          confirmed={true}
          onMixFeedback={onFeedback}
        />,
      );
      const btn = screen.getAllByRole("button", { name: /提交反馈|submit feedback/i })[0];
      fireEvent.click(btn);
      expect(onFeedback).toHaveBeenCalledWith("seg_1");
    });
  });
});
