import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { Phase6ScriptAnnotationView } from "@frontend/components/phase6/Phase6ScriptAnnotationView";
import type { AnnotationSpan } from "@frontend/types/annotation_span";

const spans: AnnotationSpan[] = [
  {
    span_id: "span_1",
    text_range: [10, 25],
    effect: "sfx_reverb",
    rationale: "营造空间感",
    narrative_role: "情绪烘托",
  },
  {
    span_id: "span_2",
    text_range: [30, 40],
    effect: "sfx_echo",
    rationale: "强调关键词",
    narrative_role: "重点标记",
  },
];

const fullText = "这是一段测试文本用于验证标注高亮功能的效果展示区域";

describe("Phase6ScriptAnnotationView", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-1: renders highlights with tooltips", () => {
    it("renders annotation spans as highlighted areas", () => {
      render(
        <Phase6ScriptAnnotationView
          fullText={fullText}
          annotationSpans={spans}
          onConfirm={vi.fn()}
        />,
      );
      const highlights = screen.getAllByTestId("annotation-highlight");
      expect(highlights).toHaveLength(spans.length);
    });

    it("shows tooltip with rationale and narrative_role on hover", () => {
      render(
        <Phase6ScriptAnnotationView
          fullText={fullText}
          annotationSpans={[spans[0]]}
          onConfirm={vi.fn()}
        />,
      );
      const highlight = screen.getByTestId("annotation-highlight");
      fireEvent.mouseEnter(highlight);
      expect(screen.getByText(/营造空间感/)).toBeInTheDocument();
      expect(screen.getByText(/情绪烘托/)).toBeInTheDocument();
    });

    it("stacks multiple triggers at same position", () => {
      const stacked: AnnotationSpan[] = [
        { ...spans[0], text_range: [10, 25] },
        { ...spans[1], text_range: [10, 25] },
      ];
      render(
        <Phase6ScriptAnnotationView
          fullText={fullText}
          annotationSpans={stacked}
          onConfirm={vi.fn()}
        />,
      );
      const badge = screen.getByTestId("stacked-badge");
      expect(badge).toBeInTheDocument();
      expect(badge.textContent).toContain("2");
    });
  });

  describe("AC-6: a11y aria-describedby", () => {
    it("highlights have aria-describedby pointing to tooltip", () => {
      render(
        <Phase6ScriptAnnotationView
          fullText={fullText}
          annotationSpans={[spans[0]]}
          onConfirm={vi.fn()}
        />,
      );
      const highlight = screen.getByTestId("annotation-highlight");
      expect(highlight).toHaveAttribute("aria-describedby");
    });

    it("confirm button has explicit aria-label", () => {
      render(
        <Phase6ScriptAnnotationView
          fullText={fullText}
          annotationSpans={spans}
          onConfirm={vi.fn()}
        />,
      );
      const btn = screen.getByRole("button", { name: /确认布局|confirm layout/i });
      expect(btn).toBeInTheDocument();
      expect(btn).toHaveAttribute("aria-label");
    });
  });
});
