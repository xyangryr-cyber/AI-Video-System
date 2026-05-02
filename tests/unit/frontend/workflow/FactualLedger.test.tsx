import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import { FactualLedger } from "@frontend/components/workflow/FactualLedger"
import type { FactualEntry } from "@frontend/components/workflow/mockData"

const facts: FactualEntry[] = [
  {
    id: "F1",
    content: "事实A",
    usage: "P1",
    source: "Source A",
    link: "https://example.com/a",
    verified: true,
    method: "x",
  },
  {
    id: "F2",
    content: "事实B",
    usage: "P2",
    source: "Source B",
    link: "https://example.com/b",
    verified: true,
    method: "y",
  },
]

describe("FactualLedger", () => {
  it("渲染所有事实条目", () => {
    render(<FactualLedger facts={facts} />)
    expect(screen.getByText("事实A")).toBeInTheDocument()
    expect(screen.getByText("事实B")).toBeInTheDocument()
    expect(screen.getByText("ID:F1")).toBeInTheDocument()
    expect(screen.getByText("ID:F2")).toBeInTheDocument()
  })

  it("外链使用 target=_blank 且 noopener noreferrer", () => {
    render(<FactualLedger facts={facts} />)
    const link = screen.getByRole("link", { name: /Source A/ })
    expect(link).toHaveAttribute("target", "_blank")
    expect(link).toHaveAttribute("rel", expect.stringContaining("noopener"))
  })

  it("展示「已核实」标签", () => {
    render(<FactualLedger facts={facts} />)
    expect(screen.getAllByText("已核实")).toHaveLength(facts.length)
  })

  it("空事实列表正常渲染（不抛错）", () => {
    render(<FactualLedger facts={[]} />)
    expect(screen.getByText("关键事实核实")).toBeInTheDocument()
  })
})
