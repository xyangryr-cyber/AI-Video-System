import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";
import { MasterAudioPlayer } from "@frontend/components/phase4/MasterAudioPlayer";
import type { GetMasterAudioResponse } from "@shared/types/api_master_audio";

const mockAudio = {
  play: vi.fn(),
  pause: vi.fn(),
  load: vi.fn(),
  addEventListener: vi.fn(),
  removeEventListener: vi.fn(),
  get currentTime() { return 0; },
  get duration() { return 0; },
  get paused() { return true; },
};

// Stub HTMLAudioElement
window.HTMLMediaElement.prototype.play = mockAudio.play;
window.HTMLMediaElement.prototype.pause = mockAudio.pause;
window.HTMLMediaElement.prototype.load = mockAudio.load;

const validMasterAudio: GetMasterAudioResponse = {
  master_audio_url: "/media/proj_1/phase4/master.mp3",
  download_url: "/api/projects/proj_1/artifacts/master_audio?phase=4&download=1",
  based_on_phase: 4,
  kind: "narration_master",
  checksum: "sha256:" + "ab".repeat(32),
  version: 1,
};

describe("MasterAudioPlayer", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-1: renders waveform / play/pause / progress", () => {
    it("renders play button when master_audio prop is provided", () => {
      render(<MasterAudioPlayer masterAudio={validMasterAudio} />);
      const btn = screen.getByRole("button", { name: /play|播放/i });
      expect(btn).toBeInTheDocument();
    });

    it("renders a progress bar element", () => {
      render(<MasterAudioPlayer masterAudio={validMasterAudio} />);
      const progress = screen.getByRole("progressbar", { name: /进度|progress/i });
      expect(progress).toBeInTheDocument();
    });

    it("renders waveform visualization area", () => {
      render(<MasterAudioPlayer masterAudio={validMasterAudio} />);
      const wave = screen.getByRole("region", { name: /主旁白播放器/i });
      expect(wave).toBeInTheDocument();
    });
  });

  describe("AC-2: download button triggers correct URL", () => {
    it("renders download link pointing to download_url", () => {
      render(<MasterAudioPlayer masterAudio={validMasterAudio} />);
      const link = screen.getByRole("link", { name: /下载|download/i });
      expect(link).toBeInTheDocument();
      expect(link).toHaveAttribute("href", validMasterAudio.download_url);
    });
  });

  describe("AC-3: re-renders on master_audio.updated", () => {
    it("accepts onUpdate prop for WS-driven refresh", () => {
      const onUpdate = vi.fn();
      const { rerender } = render(
        <MasterAudioPlayer masterAudio={validMasterAudio} onUpdate={onUpdate} />,
      );
      const updated: GetMasterAudioResponse = {
        ...validMasterAudio,
        version: 2,
        master_audio_url: "/media/proj_1/phase4/master_v2.mp3",
        download_url: "/api/projects/proj_1/artifacts/master_audio?phase=4&download=1&v=2",
        checksum: "sha256:" + "cd".repeat(32),
      };
      rerender(<MasterAudioPlayer masterAudio={updated} onUpdate={onUpdate} />);
      const link = screen.getByRole("link", { name: /下载|download/i });
      expect(link).toHaveAttribute("href", updated.download_url);
    });
  });

  describe("AC-5: a11y", () => {
    it('has role="region" and aria-label="主旁白播放器"', () => {
      render(<MasterAudioPlayer masterAudio={validMasterAudio} />);
      const region = screen.getByRole("region", { name: "主旁白播放器" });
      expect(region).toBeInTheDocument();
    });

    it("download button has aria-label", () => {
      render(<MasterAudioPlayer masterAudio={validMasterAudio} />);
      const link = screen.getByRole("link", { name: /下载/i });
      expect(link).toHaveAttribute("aria-label");
    });

    it("play button has aria-label", () => {
      render(<MasterAudioPlayer masterAudio={validMasterAudio} />);
      const btn = screen.getByRole("button", { name: /play|播放/i });
      expect(btn).toHaveAttribute("aria-label");
    });
  });

  describe("AC-6: skeleton when master_audio is missing", () => {
    it("renders skeleton when masterAudio is undefined", () => {
      const { container } = render(<MasterAudioPlayer masterAudio={undefined} />);
      const skeleton = container.querySelector('[data-testid="master-audio-skeleton"]');
      expect(skeleton).toBeInTheDocument();
    });

    it("does not render play button in skeleton state", () => {
      render(<MasterAudioPlayer masterAudio={undefined} />);
      expect(screen.queryByRole("button")).toBeNull();
    });

    it("does not crash when masterAudio is null", () => {
      const { container } = render(<MasterAudioPlayer masterAudio={null} />);
      expect(container).toBeTruthy();
    });
  });
});
