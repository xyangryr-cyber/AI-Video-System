import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Phase6Pipeline } from "@frontend/components/phase6/Phase6Pipeline";
import { usePhase6Store } from "@frontend/store/phase6_state";
import type { AnnotationSpan } from "@frontend/types/annotation_span";
import { act } from "react";

interface SegmentEntry {
  id: string;
  index: number;
  preview_url: string;
  text: string;
}

const mockAudio = { play: vi.fn().mockResolvedValue(undefined), pause: vi.fn(), load: vi.fn() };
window.HTMLMediaElement.prototype.play = mockAudio.play;
window.HTMLMediaElement.prototype.pause = mockAudio.pause;
window.HTMLMediaElement.prototype.load = mockAudio.load;

const spans: AnnotationSpan[] = [
  { span_id: "s1", text_range: [0, 10], effect: "reverb", rationale: "r1", narrative_role: "n1" },
];

const segments: SegmentEntry[] = [
  { id: "seg_1", index: 1, preview_url: "/media/seg1.mp3", text: "t1" },
];

describe("Phase6Pipeline", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    act(() => usePhase6Store.getState().reset());
  });

  describe("AC-5: enforced order Step1 -> Step2 -> Step3", () => {
    it("renders Step1 (annotation view) by default", () => {
      render(
        <Phase6Pipeline
          fullText="test text content here for annotation view"
          annotationSpans={spans}
          segments={segments}
        />,
      );
      expect(screen.getByTestId("p6-annotation-view")).toBeInTheDocument();
    });

    it("does not render Step2 until confirm layout is clicked", () => {
      render(
        <Phase6Pipeline
          fullText="test text content here for annotation view"
          annotationSpans={spans}
          segments={segments}
        />,
      );
      expect(screen.queryByTestId("segment-mix-list")).toBeNull();
    });

    it("advances to Step2 after confirm layout", () => {
      render(
        <Phase6Pipeline
          fullText="test text content here for annotation view"
          annotationSpans={spans}
          segments={segments}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /确认布局|confirm layout/i }));
      expect(screen.getByTestId("segment-mix-list")).toBeInTheDocument();
    });

    it("advances to Step3 when final master is set", () => {
      render(
        <Phase6Pipeline
          fullText="test text content here for annotation view"
          annotationSpans={spans}
          segments={segments}
        />,
      );
      fireEvent.click(screen.getByRole("button", { name: /确认布局|confirm layout/i }));
      act(() => {
        usePhase6Store.getState().setFinalMaster({
          kind: "final_audio_master",
          file_path: "/media/final.mp3",
          based_on_phase: 6,
          derived_from_segments: [],
          total_duration_seconds: 180,
          checksum: "",
          version: 1,
          source_ref: { kind: "bgm_mix_master", checksum: "" },
        });
      });
      expect(screen.getByTestId("p6-final-master")).toBeInTheDocument();
    });
  });
});
