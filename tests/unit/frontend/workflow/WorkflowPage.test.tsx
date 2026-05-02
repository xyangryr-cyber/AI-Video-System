import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter, Routes, Route } from "react-router-dom"
import { createQueryClient } from "@frontend/lib/queryClient"

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))

vi.mock("@frontend/components/previews/PhasePreviewRouter", () => ({
  PhasePreviewRouter: () => <div data-testid="preview-stub">PREVIEW</div>,
}))

import { WorkflowPage } from "@frontend/pages/WorkflowPage"
import { apiClient } from "@frontend/api/client"

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(apiClient.get).mockResolvedValue({ artifact_data: null })
})

const renderAt = (path: string) =>
  render(
    <QueryClientProvider client={createQueryClient()}>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route path="/projects/:id/phases/:phase" element={<WorkflowPage />} />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  )

describe("WorkflowPage (new UI)", () => {
  it("渲染顶部 header：项目标题、ID、阶段进度", () => {
    renderAt("/projects/proj_001/phases/12")
    expect(screen.getByText("黄金价格走势分析与投资展望")).toBeInTheDocument()
    expect(screen.getByText("proj_001")).toBeInTheDocument()
    // P12 · 最终输出
    expect(screen.getByText(/P12/)).toBeInTheDocument()
  })

  it("渲染对话历史区域（初始为空，等待用户发送）", () => {
    renderAt("/projects/proj_001/phases/12")
    expect(screen.getByPlaceholderText("发送消息给 Agent")).toBeInTheDocument()
  })

  it("渲染右栏：阶段产物 + 关键事实核实", () => {
    renderAt("/projects/proj_001/phases/12")
    expect(screen.getByText(/阶段产物/)).toBeInTheDocument()
    expect(screen.getByText("关键事实核实")).toBeInTheDocument()
  })

  it("点击阶段产物卡片打开弹窗，点击关闭按钮关闭", async () => {
    const user = userEvent.setup()
    renderAt("/projects/proj_001/phases/12")

    expect(screen.queryByTestId("artifact-modal")).toBeNull()
    await user.click(screen.getByRole("button", { name: "查看阶段 11 产物" }))
    expect(screen.getByTestId("artifact-modal")).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "关闭弹窗" }))
    expect(screen.queryByTestId("artifact-modal")).toBeNull()
  })

  it("不渲染已删除的旧功能（前进到按钮 / PhaseNavigation 左栏）", () => {
    renderAt("/projects/proj_001/phases/3")
    // 旧 UI 中存在的 advance 按钮文案（"前进到"已替换为"确认进入下一阶段"）
    expect(screen.queryByText(/前进到/)).toBeNull()
    // 旧的左侧 PhaseNavigation 文案（"流程进度"等概览标题）
    expect(screen.queryByText(/全流程进度/)).toBeNull()
  })

  it("渲染 advance 按钮（确认进入下一阶段）", () => {
    renderAt("/projects/proj_001/phases/3")
    const btn = screen.getByTestId("advance-button")
    expect(btn).toHaveTextContent("确认进入下一阶段")
    // 初始状态 gate 未满足，按钮应 disabled
    expect(btn).toBeDisabled()
  })

  it("快照：默认渲染（phase=12）", () => {
    const { asFragment } = renderAt("/projects/proj_001/phases/12")
    expect(asFragment()).toMatchSnapshot()
  })
})
