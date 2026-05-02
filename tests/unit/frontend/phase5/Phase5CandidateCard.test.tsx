import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Phase5CandidateCard } from "@frontend/components/phase5/Phase5CandidateCard";

const mockAudio = {
  play: vi.fn().mockResolvedValue(undefined),
  pause: vi.fn(),
  load: vi.fn(),
};

window.HTMLMediaElement.prototype.play = mockAudio.play;
window.HTMLMediaElement.prototype.pause = mockAudio.pause;
window.HTMLMediaElement.prototype.load = mockAudio.load;

interface BgmCandidate {
  id: string;
  preview_url: string;
  raw_bgm_url: string;
  is_recommended: boolean;
  fit_review: { verdict: "PASS" | "FAIL"; checks: number };
}

const validCandidate: BgmCandidate = {
  id: "bgm_001",
  preview_url: "/media/bgm_001/mix_preview.mp3",
  raw_bgm_url: "/media/bgm_001/raw.mp3",
  is_recommended: true,
  fit_review: { verdict: "PASS", checks: 7 },
};

describe("Phase5CandidateCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-1: renders preview and raw audio entries", () => {
    it("renders two audio buttons for preview and raw", () => {
      render(
        <Phase5CandidateCard
          candidate={validCandidate}
          isSelected={false}
          onSelect={vi.fn()}
        />,
      );
      const previewBtn = screen.getByRole("button", { name: /试听混音预览/i });
      const rawBtn = screen.getByRole("button", { name: /试听原曲/i });
      expect(previewBtn).toBeInTheDocument();
      expect(rawBtn).toBeInTheDocument();
    });

    it("renders candidate id label", () => {
      render(
        <Phase5CandidateCard
          candidate={validCandidate}
          isSelected={false}
          onSelect={vi.fn()}
        />,
      );
      expect(screen.getByText("bgm_001")).toBeInTheDocument();
    });
  });

  describe("AC-2: selecting candidate emits onSelect", () => {
    it("calls onSelect with candidate when select button clicked", () => {
      const onSelect = vi.fn();
      render(
        <Phase5CandidateCard
          candidate={validCandidate}
          isSelected={false}
          onSelect={onSelect}
        />,
      );
      const selectBtn = screen.getByRole("button", { name: /选定|select/i });
      fireEvent.click(selectBtn);
      expect(onSelect).toHaveBeenCalledWith(validCandidate);
    });
  });

  describe("AC-4: A/B switching does not break playback", () => {
    it("does not call pause on audio when switching cards", () => {
      const { rerender } = render(
        <Phase5CandidateCard
          candidate={validCandidate}
          isSelected={false}
          onSelect={vi.fn()}
        />,
      );
      rerender(
        <Phase5CandidateCard
          candidate={{ ...validCandidate, id: "bgm_002" }}
          isSelected={false}
          onSelect={vi.fn()}
        />,
      );
      expect(mockAudio.pause).not.toHaveBeenCalled();
    });
  });

  describe("AC-5: renders fit_review aggregate badge", () => {
    it("shows PASS badge when verdict is PASS", () => {
      render(
        <Phase5CandidateCard
          candidate={validCandidate}
          isSelected={false}
          onSelect={vi.fn()}
        />,
      );
      expect(screen.getByText(/PASS|通过/)).toBeInTheDocument();
    });

    it("shows FAIL badge when verdict is FAIL", () => {
      const failCandidate = {
        ...validCandidate,
        fit_review: { verdict: "FAIL" as const, checks: 3 },
      };
      render(
        <Phase5CandidateCard
          candidate={failCandidate}
          isSelected={false}
          onSelect={vi.fn()}
        />,
      );
      expect(screen.getByText(/FAIL|未通过/)).toBeInTheDocument();
    });
  });

  describe("AC-6: a11y role and aria-pressed", () => {
    it('has role="article" on card container', () => {
      render(
        <Phase5CandidateCard
          candidate={validCandidate}
          isSelected={false}
          onSelect={vi.fn()}
        />,
      );
      expect(screen.getByRole("article")).toBeInTheDocument();
    });

    it('has aria-pressed true when selected', () => {
      render(
        <Phase5CandidateCard
          candidate={validCandidate}
          isSelected={true}
          onSelect={vi.fn()}
        />,
      );
      const card = screen.getByRole("article");
      expect(card).toHaveAttribute("aria-pressed", "true");
    });

    it('has aria-pressed false when not selected', () => {
      render(
        <Phase5CandidateCard
          candidate={validCandidate}
          isSelected={false}
          onSelect={vi.fn()}
        />,
      );
      const card = screen.getByRole("article");
      expect(card).toHaveAttribute("aria-pressed", "false");
    });
  });
});
