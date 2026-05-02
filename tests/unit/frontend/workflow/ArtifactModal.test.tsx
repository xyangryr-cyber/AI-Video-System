import { describe, it, expect, vi, beforeEach } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClientProvider } from "@tanstack/react-query"
import { createQueryClient } from "@frontend/lib/queryClient"

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}))

vi.mock("@frontend/components/previews/PhasePreviewRouter", () => ({
  PhasePreviewRouter: ({ phase }: { phase: number }) => (
    <div data-testid="preview-stub">PREVIEW_PHASE_{phase}</div>
  ),
}))

import { ArtifactModal } from "@frontend/components/workflow/ArtifactModal"
import { apiClient } from "@frontend/api/client"

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(apiClient.get).mockResolvedValue({ artifact_data: null })
})

const renderModal = (props: {
  open: boolean
  phaseIndex?: number
  phaseLabel?: string
  onClose?: () => void
}) =>
  render(
    <QueryClientProvider client={createQueryClient()}>
      <ArtifactModal
        open={props.open}
        projectId="proj_001"
        phaseIndex={props.phaseIndex ?? 3}
        phaseLabel={props.phaseLabel ?? "脚本润色"}
        onClose={props.onClose ?? (() => {})}
      />
    </QueryClientProvider>,
  )

describe("ArtifactModal", () => {
  it("open=false 不渲染 modal", () => {
    renderModal({ open: false })
    expect(screen.queryByTestId("artifact-modal")).toBeNull()
  })

  it("open=true 渲染 modal 并展示阶段标题与 phase 编号", () => {
    renderModal({ open: true, phaseIndex: 5, phaseLabel: "背景音乐" })
    expect(screen.getByTestId("artifact-modal")).toBeInTheDocument()
    expect(screen.getByText(/P5/)).toBeInTheDocument()
    expect(screen.getByText("背景音乐")).toBeInTheDocument()
  })

  it("点击 backdrop 触发 onClose", async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    renderModal({ open: true, onClose })
    await user.click(screen.getByTestId("modal-backdrop"))
    expect(onClose).toHaveBeenCalled()
  })

  it("点击关闭按钮触发 onClose", async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()
    renderModal({ open: true, onClose })
    await user.click(screen.getByRole("button", { name: "关闭弹窗" }))
    expect(onClose).toHaveBeenCalled()
  })

  it("内部渲染 PhasePreviewRouter 并传入 phase 索引", () => {
    renderModal({ open: true, phaseIndex: 7 })
    expect(screen.getByTestId("preview-stub")).toHaveTextContent("PREVIEW_PHASE_7")
  })
})
