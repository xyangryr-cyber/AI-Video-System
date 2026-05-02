import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { Phase6FinalMaster } from "@frontend/components/phase6/Phase6FinalMaster";
import type { MasterAudioView } from "@frontend/types/audio_master";

const finalMaster: MasterAudioView = {
  kind: "final_audio_master",
  file_path: "/media/final.mp3",
  based_on_phase: 6,
  derived_from_segments: ["seg_1", "seg_2"],
  total_duration_seconds: 180,
  checksum: "sha256:" + "ab".repeat(32),
  version: 1,
  source_ref: { kind: "bgm_mix_master", checksum: "sha256:" + "cd".repeat(32) },
};

describe("Phase6FinalMaster", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-4: only renders when kind is final_audio_master", () => {
    it("renders when master_audio kind is final_audio_master", () => {
      render(<Phase6FinalMaster masterAudio={finalMaster} />);
      expect(screen.getByTestId("p6-final-master")).toBeInTheDocument();
    });

    it("renders download link", () => {
      render(<Phase6FinalMaster masterAudio={finalMaster} />);
      const link = screen.getByRole("link", { name: /下载|download/i });
      expect(link).toHaveAttribute("href", finalMaster.file_path);
    });

    it("does not render when masterAudio is null", () => {
      const { container } = render(<Phase6FinalMaster masterAudio={null} />);
      expect(container.querySelector('[data-testid="p6-final-master"]')).toBeNull();
    });

    it("does not render for non-final kind", () => {
      const nonFinal: MasterAudioView = {
        ...finalMaster,
        kind: "bgm_mix_master",
      };
      const { container } = render(<Phase6FinalMaster masterAudio={nonFinal} />);
      expect(container.querySelector('[data-testid="p6-final-master"]')).toBeNull();
    });
  });
});
