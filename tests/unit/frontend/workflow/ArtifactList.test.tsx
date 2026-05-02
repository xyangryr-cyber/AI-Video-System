import { describe, it, expect, vi } from "vitest"
import { render, screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { ArtifactList } from "@frontend/components/workflow/ArtifactList"

const PHASES = ["需求定义", "内容主线", "口播脚本", "脚本润色"] as const

describe("ArtifactList", () => {
  it("仅渲染 0..currentPhase 的卡片，按倒序排列（最新在最上）", () => {
    render(<ArtifactList phaseLabels={PHASES} currentPhase={2} onSelect={() => {}} />)
    const list = screen.getByTestId("artifact-list")
    const buttons = within(list).getAllByRole("button")
    // 倒序：phase 2, 1, 0；phase 3 不渲染
    expect(buttons).toHaveLength(3)
    expect(buttons[0]).toHaveTextContent("PHASE 2")
    expect(buttons[1]).toHaveTextContent("PHASE 1")
    expect(buttons[2]).toHaveTextContent("PHASE 0")
  })

  it("当前 phase 卡片显示 In Progress 标签", () => {
    render(<ArtifactList phaseLabels={PHASES} currentPhase={2} onSelect={() => {}} />)
    const badges = screen.getAllByTestId("in-progress-badge")
    expect(badges).toHaveLength(1)
    expect(badges[0]).toHaveTextContent(/in progress/i)
  })

  it("点击产物卡片触发 onSelect 并传入对应 phase index", async () => {
    const user = userEvent.setup()
    const onSelect = vi.fn()
    render(<ArtifactList phaseLabels={PHASES} currentPhase={2} onSelect={onSelect} />)

    await user.click(screen.getByRole("button", { name: "查看阶段 1 产物" }))
    expect(onSelect).toHaveBeenCalledWith(1)
  })
})
