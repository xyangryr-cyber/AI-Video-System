import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@frontend/hooks/useProjects", () => ({
  useProjects: () => ({
    data: [
      {
        id: "proj_001",
        project_id: "proj_001",
        title: "黄金价格走势分析",
        category: "行业分析",
        current_phase: 2,
        latest_reached_phase: 5,
        progress: 45,
        status: "in_progress",
        updated_at: new Date().toISOString(),
      },
      {
        id: "proj_002",
        project_id: "proj_002",
        title: "十五五规划解读",
        category: "政策解读",
        current_phase: 1,
        latest_reached_phase: 1,
        progress: 15,
        status: "awaiting_user",
        updated_at: new Date(Date.now() - 7200000).toISOString(),
      },
      {
        id: "proj_003",
        project_id: "proj_003",
        title: "AI 行业周报",
        category: "行业分析",
        current_phase: 8,
        latest_reached_phase: 8,
        progress: 70,
        status: "completed",
        updated_at: new Date(Date.now() - 86400000).toISOString(),
      },
    ],
    isLoading: false,
    isError: false,
  }),
}));

import { ProjectList } from "@frontend/pages/ProjectList";

function createQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false },
    },
  });
}

function renderWithProviders() {
  const qc = createQueryClient();
  return render(
    <QueryClientProvider client={qc}>
      <MemoryRouter>
        <ProjectList />
      </MemoryRouter>
    </QueryClientProvider>
  );
}

describe("ProjectList visual alignment", () => {
  it("renders the Chinese header 'AI 视频制作系统'", () => {
    renderWithProviders();
    expect(screen.getByText("AI 视频制作系统")).toBeDefined();
  });

  it("renders the subtitle text", () => {
    renderWithProviders();
    expect(screen.getByText(/面向金融内容创作者/)).toBeDefined();
  });

  it("renders a table with 6 column headers in Chinese", () => {
    renderWithProviders();
    const headers = ["标题", "分类", "阶段", "进度", "状态", "更新时间"];
    for (const h of headers) {
      expect(screen.getByText(h)).toBeDefined();
    }
  });

  it("renders '新建项目' button with blue background", () => {
    renderWithProviders();
    const btn = screen.getByRole("button", { name: /新建项目/ });
    expect(btn).toBeDefined();
    expect(btn.className).toMatch(/bg-blue-600/);
  });

  it("renders the 'M3: 项目管理列表' section label", () => {
    renderWithProviders();
    expect(screen.getByText("M3: 项目管理列表")).toBeDefined();
  });

  it("renders status icons with Chinese text", () => {
    renderWithProviders();
    expect(screen.getByText("进行中")).toBeDefined();
    expect(screen.getByText("等用户")).toBeDefined();
    expect(screen.getByText("完成")).toBeDefined();
  });

  it("renders category pill badges with rounded-full", () => {
    renderWithProviders();
    const badges = screen.getAllByText("行业分析");
    expect(badges.length).toBeGreaterThanOrEqual(1);
    expect(badges[0].className).toMatch(/rounded-full/);
  });

  it("renders progress bars with h-1.5 and bg-blue-600", () => {
    renderWithProviders();
    const progressFills = document.querySelectorAll("[class*='bg-blue-600'][class*='h-1.5']");
    expect(progressFills.length).toBeGreaterThan(0);
  });

  it("renders relative time for updated_at", () => {
    renderWithProviders();
    const cells = document.querySelectorAll("td");
    const timeTexts = Array.from(cells)
      .map((c) => c.textContent)
      .filter((t) => t?.includes("前") || t?.includes("秒"));
    expect(timeTexts.length).toBeGreaterThan(0);
  });

  it("has settings button with lucide Settings icon", () => {
    renderWithProviders();
    const buttons = screen.getAllByRole("button");
    const settingsBtn = buttons.find(
      (b) => b.getAttribute("aria-label") === "Settings"
    );
    expect(settingsBtn).toBeDefined();
  });

  it("renders project titles in the table", () => {
    renderWithProviders();
    expect(screen.getByText("黄金价格走势分析")).toBeDefined();
    expect(screen.getByText("十五五规划解读")).toBeDefined();
    expect(screen.getByText("AI 行业周报")).toBeDefined();
  });

  it("renders phase numbers", () => {
    renderWithProviders();
    expect(screen.getByText("Phase 2")).toBeDefined();
    expect(screen.getByText("Phase 1")).toBeDefined();
    expect(screen.getByText("Phase 8")).toBeDefined();
  });
});
