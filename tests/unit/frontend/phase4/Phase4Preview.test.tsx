import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { Phase4Preview } from "@frontend/components/phase4/Phase4Preview";
import type { GetMasterAudioResponse } from "@shared/types/api_master_audio";

const validMasterAudio: GetMasterAudioResponse = {
  master_audio_url: "/media/proj_1/phase4/master.mp3",
  download_url: "/api/projects/proj_1/artifacts/master_audio?phase=4&download=1",
  based_on_phase: 4,
  kind: "narration_master",
  checksum: "sha256:" + "ab".repeat(32),
  version: 1,
};

describe("Phase4Preview", () => {
  describe("AC-1 integration: embeds MasterAudioPlayer in top slot", () => {
    it("renders MasterAudioPlayer when masterAudio prop provided", () => {
      render(
        <Phase4Preview masterAudio={validMasterAudio}>
          <div data-testid="segment-revise-panel">Segment Revise Panel</div>
        </Phase4Preview>,
      );
      const region = screen.getByRole("region", { name: "主旁白播放器" });
      expect(region).toBeInTheDocument();
    });

    it("renders children (segment revise panel) alongside player", () => {
      render(
        <Phase4Preview masterAudio={validMasterAudio}>
          <div data-testid="segment-revise-panel">Segment Revise</div>
        </Phase4Preview>,
      );
      expect(screen.getByTestId("segment-revise-panel")).toBeInTheDocument();
      const region = screen.getByRole("region", { name: "主旁白播放器" });
      expect(region).toBeInTheDocument();
    });
  });

  describe("AC-4: v3.15 segment revise panel not regressed", () => {
    it("renders segment revise panel when children provided", () => {
      render(
        <Phase4Preview masterAudio={undefined}>
          <div data-testid="segment-revise-panel">Segment Revise Panel v3.15</div>
        </Phase4Preview>,
      );
      expect(screen.getByTestId("segment-revise-panel")).toBeInTheDocument();
      expect(screen.getByText(/Segment Revise Panel v3.15/)).toBeInTheDocument();
    });

    it("shows skeleton in top slot but still renders children when audio missing", () => {
      render(
        <Phase4Preview masterAudio={undefined}>
          <div data-testid="segment-revise-panel">Segments</div>
        </Phase4Preview>,
      );
      const skeleton = document.querySelector('[data-testid="master-audio-skeleton"]');
      expect(skeleton).toBeInTheDocument();
      expect(screen.getByTestId("segment-revise-panel")).toBeInTheDocument();
    });
  });
});
