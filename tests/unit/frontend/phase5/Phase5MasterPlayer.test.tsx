import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { Phase5MasterPlayer } from "@frontend/components/phase5/Phase5MasterPlayer";
import type { MasterAudioView } from "@frontend/types/audio_master";

const mockAudio = {
  play: vi.fn().mockResolvedValue(undefined),
  pause: vi.fn(),
  load: vi.fn(),
};

window.HTMLMediaElement.prototype.play = mockAudio.play;
window.HTMLMediaElement.prototype.pause = mockAudio.pause;
window.HTMLMediaElement.prototype.load = mockAudio.load;

const bgmMaster: MasterAudioView = {
  kind: "bgm_mix_master",
  file_path: "/media/proj_1/phase5/master_bgm.mp3",
  based_on_phase: 5,
  derived_from_segments: ["seg_1"],
  total_duration_seconds: 120,
  checksum: "sha256:" + "ab".repeat(32),
  version: 1,
  source_ref: {
    kind: "narration_master",
    checksum: "sha256:" + "cd".repeat(32),
  },
};

const narrationMaster: MasterAudioView = {
  kind: "narration_master",
  file_path: "/media/proj_1/phase5/narration.mp3",
  based_on_phase: 5,
  derived_from_segments: ["seg_1"],
  total_duration_seconds: 120,
  checksum: "sha256:" + "ab".repeat(32),
  version: 1,
};

describe("Phase5MasterPlayer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-2: MasterPlayer appears with download when master_audio is set", () => {
    it("renders audio element with master file_path", () => {
      render(<Phase5MasterPlayer masterAudio={bgmMaster} />);
      const region = screen.getByRole("region", { name: /P5.*播放|master.*player/i });
      expect(region).toBeInTheDocument();
    });

    it("renders download link", () => {
      render(<Phase5MasterPlayer masterAudio={bgmMaster} />);
      const link = screen.getByRole("link", { name: /下载|download/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute("href", bgmMaster.file_path);
    });

    it("does not render when masterAudio is null", () => {
      const { container } = render(<Phase5MasterPlayer masterAudio={null} />);
      expect(container.querySelector('[data-testid="p5-master-player"]')).toBeNull();
    });
  });

  describe("AC-3: no BGM falls back to narration_master", () => {
    it("renders narration_master when kind is narration_master", () => {
      render(<Phase5MasterPlayer masterAudio={narrationMaster} />);
      const region = screen.getByRole("region", { name: /P5.*播放|master.*player/i });
      expect(region).toBeInTheDocument();
    });
  });

  describe("AC-6: a11y", () => {
    it("play button has aria-label", () => {
      render(<Phase5MasterPlayer masterAudio={bgmMaster} />);
      const btn = screen.getByRole("button", { name: /play|播放/i });
      expect(btn).toHaveAttribute("aria-label");
    });

    it("has role region", () => {
      render(<Phase5MasterPlayer masterAudio={bgmMaster} />);
      expect(screen.getByRole("region", { name: /P5.*播放|master.*player/i })).toBeInTheDocument();
    });
  });
});
