/**
 * [VIS-001] P0, P1, P2 Phase Preview visual alignment tests.
 *
 * Verifies P0RequirementsView, P1ScriptView, P2SegmentView render
 * with the correct visual structure matching prototype PhaseViews.
 */
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { P0RequirementsView } from "@frontend/components/previews/P0RequirementsView";
import { P1ScriptView } from "@frontend/components/previews/P1ScriptView";
import { P2SegmentView } from "@frontend/components/previews/P2SegmentView";
import type { ScriptSegment } from "@frontend/types/preview";

// ---------------------------------------------------------------------------
// P0RequirementsView
// ---------------------------------------------------------------------------
describe("P0RequirementsView visual alignment", () => {
  it("empty state: shows Chinese label '暂无需求数据'", () => {
    render(<P0RequirementsView />);
    expect(screen.getByText("暂无需求数据")).toBeDefined();
  });

  it("empty state: shows helper description about Agent init", () => {
    render(<P0RequirementsView />);
    expect(screen.getByText(/等待需求采集 Agent 完成初始化/)).toBeDefined();
  });

  it("empty state: uses empty-state container styling (flex, items-center, justify-center, text-slate-400)", () => {
    render(<P0RequirementsView />);
    const container = screen.getByTestId("preview-p0");
    expect(container.className).toMatch(/flex/);
    expect(container.className).toMatch(/items-center/);
    expect(container.className).toMatch(/justify-center/);
    expect(container.className).toMatch(/text-slate-400/);
  });

  it("with data: renders 2x2 grid layout with gap-4", () => {
    render(<P0RequirementsView requirements={{ title: "test", description: "test desc" }} />);
    const grid = document.querySelector(".grid.grid-cols-2");
    expect(grid).toBeTruthy();
    expect(grid?.className).toMatch(/gap-4/);
  });

  it("with data: renders info cards with border-2 border-slate-200 rounded-xl", () => {
    render(<P0RequirementsView requirements={{ title: "test" }} />);
    const cards = document.querySelectorAll(".border-2.border-slate-200.rounded-xl");
    expect(cards.length).toBeGreaterThanOrEqual(3);
  });

  it("with data: shows Chinese label '主题 / 标题'", () => {
    render(<P0RequirementsView requirements={{ title: "test" }} />);
    expect(screen.getByText("主题 / 标题")).toBeDefined();
  });

  it("with data: shows Chinese label '分类定位'", () => {
    render(<P0RequirementsView requirements={{ category: "finance" }} />);
    expect(screen.getByText("分类定位")).toBeDefined();
  });

  it("with data: shows Chinese label '目标受众时长'", () => {
    render(<P0RequirementsView requirements={{ target_duration: "5min" }} />);
    expect(screen.getByText("目标受众时长")).toBeDefined();
  });

  it("with data: shows Chinese label '发布平台策略'", () => {
    render(<P0RequirementsView requirements={{ platforms: "Bilibili" }} />);
    expect(screen.getByText("发布平台策略")).toBeDefined();
  });

  it("with data: section labels use uppercase tracking-wider text-xs text-slate-500", () => {
    render(<P0RequirementsView requirements={{ title: "test" }} />);
    const label = screen.getByText("主题 / 标题");
    expect(label.className).toMatch(/text-xs/);
    expect(label.className).toMatch(/text-slate-500/);
    expect(label.className).toMatch(/uppercase/);
    expect(label.className).toMatch(/tracking-wider/);
  });

  it("with data: renders section label '核心提点与需求描述'", () => {
    render(<P0RequirementsView requirements={{ title: "test" }} />);
    expect(screen.getByText("核心提点与需求描述")).toBeDefined();
  });

  it("with data: description area has bg-slate-50 styling", () => {
    render(<P0RequirementsView requirements={{ description: "test description" }} />);
    const desc = document.querySelector(".bg-slate-50");
    expect(desc).toBeTruthy();
  });

  it("with data: uses title field from requirements", () => {
    render(<P0RequirementsView requirements={{ title: "gold analysis" }} />);
    expect(screen.getByText("gold analysis")).toBeDefined();
  });

  it("with data: uses core_brief as description fallback", () => {
    render(<P0RequirementsView requirements={{ core_brief: "core brief text" }} />);
    expect(screen.getByText("core brief text")).toBeDefined();
  });

  it("with data: platform splits comma-separated string into badges", () => {
    render(<P0RequirementsView requirements={{ platforms: "Bilibili,Douyin" }} />);
    expect(screen.getByText(/Bilibili/)).toBeDefined();
    expect(screen.getByText(/Douyin/)).toBeDefined();
  });

  it("with data: first platform badge uses blue-100/blue-700 accent styling", () => {
    render(<P0RequirementsView requirements={{ platforms: "Bilibili,Douyin" }} />);
    const badges = screen.getAllByText(/Bilibili|Douyin/);
    const firstBadge = badges[0];
    expect(firstBadge.className).toMatch(/bg-blue-100/);
    expect(firstBadge.className).toMatch(/text-blue-700/);
  });

  it("with data: secondary platform badge uses slate-100/slate-700 styling", () => {
    render(<P0RequirementsView requirements={{ platforms: "Bilibili,Douyin" }} />);
    const badges = screen.getAllByText(/Bilibili|Douyin/);
    const secondBadge = badges[1];
    expect(secondBadge.className).toMatch(/bg-slate-100/);
    expect(secondBadge.className).toMatch(/text-slate-700/);
  });

  it("with data: platform badge has rounded-md text-xs px-2 py-0.5", () => {
    render(<P0RequirementsView requirements={{ platforms: "Bilibili" }} />);
    const badge = screen.getByText(/Bilibili/);
    expect(badge.className).toMatch(/rounded-md/);
    expect(badge.className).toMatch(/text-xs/);
    expect(badge.className).toMatch(/px-2/);
  });
});

// ---------------------------------------------------------------------------
// P1ScriptView
// ---------------------------------------------------------------------------
describe("P1ScriptView visual alignment", () => {
  it("empty state: shows Chinese label '暂无脚本内容'", () => {
    render(<P1ScriptView />);
    expect(screen.getByText("暂无脚本内容")).toBeDefined();
  });

  it("empty state: shows helper description about Agent init", () => {
    render(<P1ScriptView />);
    expect(screen.getByText(/等待脚本生成 Agent 完成/)).toBeDefined();
  });

  it("empty state: uses empty-state container styling (flex, items-center, justify-center, text-slate-400)", () => {
    render(<P1ScriptView />);
    const container = screen.getByTestId("preview-p1");
    expect(container.className).toMatch(/text-slate-400/);
    expect(container.className).toMatch(/flex/);
    expect(container.className).toMatch(/items-center/);
    expect(container.className).toMatch(/justify-center/);
  });

  it("with content: renders numbered section cards", () => {
    render(<P1ScriptView content="# Section 1\nContent 1\n# Section 2\nContent 2" />);
    const cards = document.querySelectorAll(".border-2.border-slate-200.rounded-xl");
    expect(cards.length).toBeGreaterThanOrEqual(1);
  });

  it("with content: cards have left accent bar (w-1 absolute left-0 bg-blue-500)", () => {
    render(<P1ScriptView content="# Section 1\nContent 1" />);
    const accent = document.querySelector(".bg-blue-500.w-1");
    expect(accent).toBeTruthy();
  });

  it("with content: renders number badge with blue styling (bg-blue-50 text-blue-600)", () => {
    render(<P1ScriptView content="# Section 1\nContent 1" />);
    const badge = document.querySelector(".bg-blue-50.text-blue-600");
    expect(badge).toBeTruthy();
  });

  it("with content: number badge shows correct sequence (1 for first)", () => {
    render(<P1ScriptView content="# First section\nContent" />);
    const badge = screen.getByText("1");
    expect(badge).toBeDefined();
  });

  it("with versions: shows version badge with purple styling", () => {
    render(<P1ScriptView content="# Test" versions={3} />);
    const badge = screen.getByText(/v3/);
    expect(badge).toBeDefined();
    expect(badge.className).toMatch(/bg-purple-100/);
    expect(badge.className).toMatch(/text-purple-700/);
  });

  it("with content: renders titles extracted from markdown headings", () => {
    render(<P1ScriptView content={"# Chapter 1: intro\nContent text"} />);
    expect(screen.getByText(/Chapter 1: intro/)).toBeDefined();
  });

  it("with content: renders description text below titles", () => {
    render(<P1ScriptView content={"# Title\nSome description here"} />);
    expect(screen.getByText(/Some description here/)).toBeDefined();
  });

  it("with plain text (no markdown): renders as single section", () => {
    render(<P1ScriptView content="Plain text content with no heading" />);
    expect(screen.getByText(/Plain text content with no heading/)).toBeDefined();
  });
});

// ---------------------------------------------------------------------------
// P2SegmentView
// ---------------------------------------------------------------------------
const mockP2Segments: ScriptSegment[] = [
  {
    id: "seg_1",
    content: "Do you remember how cheap gold was last year?",
    key_data_points: [],
  },
  {
    id: "seg_2",
    content: "WGC data shows Q1 2025 central bank gold purchases hit a record 290 tons.",
    key_data_points: [
      {
        data_point_id: "dp_1",
        label: "Central bank net purchases",
        value: "290 tons",
        unit: "tons",
        source: "WGC 2025Q1 Report",
        trust_level: "source_verified",
        segment_id: "seg_2",
      },
    ],
  },
];

describe("P2SegmentView visual alignment", () => {
  it("empty state: shows Chinese label '暂无分段数据'", () => {
    render(<P2SegmentView />);
    expect(screen.getByText("暂无分段数据")).toBeDefined();
  });

  it("empty state: shows helper description about Agent init", () => {
    render(<P2SegmentView />);
    expect(screen.getByText(/等待脚本分段 Agent 完成/)).toBeDefined();
  });

  it("empty state: uses empty-state container styling (flex, items-center, justify-center, text-slate-400)", () => {
    render(<P2SegmentView />);
    const container = screen.getByTestId("preview-p2");
    expect(container.className).toMatch(/text-slate-400/);
    expect(container.className).toMatch(/flex/);
    expect(container.className).toMatch(/items-center/);
    expect(container.className).toMatch(/justify-center/);
  });

  it("with segments: renders dark header bar with bg-slate-800 text-white", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    const header = document.querySelector(".bg-slate-800");
    expect(header).toBeTruthy();
    expect(header?.className).toMatch(/text-white/);
  });

  it("with segments: shows segment content text", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    expect(screen.getByText(/cheap gold/)).toBeDefined();
  });

  it("with segments: shows word count (字) in header bar", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    const elements = screen.getAllByText(/字/);
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it("with segments: shows duration estimate (秒) in header bar", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    const elements = screen.getAllByText(/秒/);
    expect(elements.length).toBeGreaterThanOrEqual(1);
  });

  it("with segments: segment card has border-2 border-slate-200 rounded-xl overflow-hidden", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    const card = document.querySelector(".border-2.border-slate-200.rounded-xl.overflow-hidden");
    expect(card).toBeTruthy();
  });

  it("with segments: renders FactChecker section for segments with data points", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    expect(screen.getByText("关键数据点核查")).toBeDefined();
  });

  it("with segments: verified data point shows source info", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    expect(screen.getByText(/WGC 2025Q1/)).toBeDefined();
  });

  it("with segments: verified badge uses green styling", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    const verified = screen.getByText("Verified");
    expect(verified).toBeDefined();
    expect(verified.className).toMatch(/bg-green-100/);
    expect(verified.className).toMatch(/text-green-700/);
  });

  it("with segments: shows '重写此段' button on segments with data points", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    expect(screen.getByText("重写此段")).toBeDefined();
  });

  it("with segments: data point shows label and value", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    expect(screen.getByText(/Central bank net purchases/)).toBeDefined();
    expect(screen.getByText(/290 tons/)).toBeDefined();
  });

  it("with segments: segment header shows sequence number", () => {
    render(<P2SegmentView segments={mockP2Segments} />);
    expect(screen.getByText(/段落 1/)).toBeDefined();
    expect(screen.getByText(/段落 2/)).toBeDefined();
  });
});
