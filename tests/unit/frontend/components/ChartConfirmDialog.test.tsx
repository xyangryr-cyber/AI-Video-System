import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { ChartConfirmDialog } from "@frontend/components/ChartConfirmDialog";
import type { ChartIntent, StyleLock } from "@frontend/components/ChartConfirmDialog";

const mockStyleLock: StyleLock = {
  project_id: "proj_test",
  locked_at: "2026-01-01T00:00:00Z",
  locked_by: "user_confirmed" as const,
  color_palette: {
    primary: "#1a1a2e",
    secondary: "#16213e",
    accent: "#0f3460",
    background: "#e94560",
  },
  font_family: "sans-serif",
  chart_style: {
    axis_color: "#333",
    grid_color: "#ddd",
    label_font_size: 12,
  },
};

function makeIntent(overrides: Partial<ChartIntent> = {}): ChartIntent {
  return {
    id: "ci_test",
    status: "awaiting_confirmation",
    clarification_questions: [],
    data_preview: {
      chart_type: "line",
      time_range: "2026-01-01 to 2026-03-31",
      frequency: "daily",
      unit: "USD",
      source_label: "Yahoo Finance",
    },
    data_source_verified: true,
    axis_config: {
      x_axis: { label: "Date", unit: "", zero_based: false },
      y_axis: { label: "Price", unit: "USD", min: 0, max: 100, zero_based: true },
    },
    style_config: {
      line_width: 2,
      line_color: "#1a1a2e",
      smooth: false,
      background_color: "#ffffff",
      grid_visible: true,
      show_source_label: false,
      animation_duration_ms: 500,
    },
    ...overrides,
  };
}

describe("ChartConfirmDialog - AC-1: clarification limits and priority", () => {
  it("displays max 2 questions when clarification_questions has 5 items", () => {
    const questions = [
      "What entity do you want to chart?",
      "What time range should the chart cover?",
      "What unit should the y-axis use?",
      "What granularity do you prefer?",
      "Which stock symbol should we track?",
    ];
    const intent = makeIntent({
      status: "awaiting_clarification",
      clarification_questions: questions,
      data_preview: undefined,
    });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    const inputs = screen.getAllByRole("textbox");
    expect(inputs.length).toBeLessThanOrEqual(2);
  });

  it("prioritizes time_range/granularity questions over entity and unit", () => {
    const questions = [
      "What entity do you want to chart?",
      "What time range should the chart cover?",
      "What unit should the y-axis use?",
      "What granularity do you prefer?",
      "Which stock symbol should we track?",
    ];
    const intent = makeIntent({
      status: "awaiting_clarification",
      clarification_questions: questions,
      data_preview: undefined,
    });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    const labels = screen.getAllByRole("textbox");
    expect(labels.length).toBe(2);
    // The first two should be time_range and granularity (highest priority)
    const allText = document.body.textContent || "";
    const timePos = allText.indexOf("time range");
    const granularityPos = allText.indexOf("granularity");
    const entityPos = allText.indexOf("entity");
    const unitPos = allText.indexOf("unit");

    // time_range and granularity should appear, entity and unit should not
    expect(timePos).toBeGreaterThanOrEqual(0);
    expect(granularityPos).toBeGreaterThanOrEqual(0);
    expect(entityPos).toBe(-1);
    expect(unitPos).toBe(-1);
  });
});

describe("ChartConfirmDialog - AC-2: unverified source badge red and confirm disabled", () => {
  it("shows red badge and disables confirm button when data_source_verified is false", () => {
    const intent = makeIntent({ data_source_verified: false });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    const badge = screen.getByText(/未验证|unverified/i);
    expect(badge).toBeInTheDocument();
    expect(badge.className).toMatch(/red|danger|bg-red/i);

    const confirmBtn = screen.getByRole("button", { name: /确认渲染|confirm render/i });
    expect(confirmBtn).toBeDisabled();
  });

  it("shows green badge and enabled confirm button when data_source_verified is true", () => {
    const intent = makeIntent({ data_source_verified: true });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    const badge = screen.getByText(/已验证|verified/i);
    expect(badge).toBeInTheDocument();
    expect(badge.className).toMatch(/green|success|bg-green/i);

    const confirmBtn = screen.getByRole("button", { name: /确认渲染|confirm render/i });
    expect(confirmBtn).not.toBeDisabled();
  });
});

describe("ChartConfirmDialog - AC-3: color picker restricted to style_lock.color_palette", () => {
  it("only renders color options from style_lock.color_palette values", () => {
    const intent = makeIntent({ data_source_verified: true });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    // Color picker should have options matching palette values
    const paletteValues = Object.values(mockStyleLock.color_palette);
    for (const color of paletteValues) {
      // Each palette color should be present in the DOM (as swatch buttons with data-color attr)
      const found = document.body.innerHTML.includes(color);
      expect(found).toBe(true);
    }

    // A non-palette color should NOT have interactive options
    const nonPaletteColor = "#ff0000";
    const nonPaletteFound = document.querySelectorAll(`[data-color="${nonPaletteColor}"]`).length;
    expect(nonPaletteFound).toBe(0);
  });
});

describe("ChartConfirmDialog - AC-4: five state transitions render correct UI", () => {
  it("awaiting_clarification: shows questions list + text inputs, no data preview", () => {
    const intent = makeIntent({
      status: "awaiting_clarification",
      clarification_questions: ["What time range?"],
      data_preview: undefined,
    });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    expect(screen.getByRole("textbox")).toBeInTheDocument();
    expect(screen.queryByText(/data preview|数据预览/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/source|来源/i)).not.toBeInTheDocument();
  });

  it("awaiting_confirmation: shows data preview, source badge, axis editor, style editor, buttons", () => {
    const intent = makeIntent({
      status: "awaiting_confirmation",
      data_source_verified: true,
    });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    expect(screen.getByText("来源:")).toBeInTheDocument();
    expect(screen.getByText("坐标轴")).toBeInTheDocument();
    expect(screen.getByText("样式")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /确认渲染|confirm render/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /上一步澄清/ })).toBeInTheDocument();
  });

  it("rendering: shows progress indicator, all interactive elements disabled", () => {
    const intent = makeIntent({ status: "rendering" });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    expect(screen.getByText(/rendering|渲染中|progress/i)).toBeInTheDocument();
    // Confirm button should not be interactable
    const confirmBtn = screen.queryByRole("button", { name: /确认渲染|confirm render/i });
    if (confirmBtn) {
      expect(confirmBtn).toBeDisabled();
    }
  });

  it("done: shows success message and close button", () => {
    const intent = makeIntent({ status: "done" });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: /完成/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /close|关闭/i })).toBeInTheDocument();
  });

  it("cancelled: shows cancel message and close button", () => {
    const intent = makeIntent({ status: "cancelled" });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
        onBackToClarify={vi.fn()}
      />,
    );

    expect(screen.getByRole("heading", { name: /已取消/ })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /close|关闭/i })).toBeInTheDocument();
  });

  it("calls onConfirm with overrides when confirm is clicked in awaiting_confirmation", async () => {
    const onConfirm = vi.fn();
    const intent = makeIntent({
      status: "awaiting_confirmation",
      data_source_verified: true,
    });
    render(
      <ChartConfirmDialog
        open={true}
        chart_intent={intent}
        style_lock={mockStyleLock}
        onClose={vi.fn()}
        onConfirm={onConfirm}
        onBackToClarify={vi.fn()}
      />,
    );

    await userEvent.click(screen.getByRole("button", { name: /确认渲染|confirm render/i }));
    expect(onConfirm).toHaveBeenCalledOnce();
  });
});
