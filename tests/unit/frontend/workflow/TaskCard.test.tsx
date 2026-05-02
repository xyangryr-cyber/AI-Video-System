import { describe, it, expect } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { TaskCard } from "@frontend/components/workflow/TaskCard"
import type { WorkflowTask } from "@frontend/components/workflow/mockData"

const tasks: WorkflowTask[] = [
  { title: "提取核心信息和视频需求", completed: true },
  { title: "基于需求生成基础大纲", completed: true },
  { title: "向用户报告并发送APP集成清单", completed: false },
]

describe("TaskCard", () => {
  it("默认折叠：任务列表不渲染", () => {
    render(<TaskCard currentTaskTitle="向用户报告并发送APP集成清单" tasks={tasks} />)
    expect(screen.queryByTestId("task-list")).toBeNull()
    expect(screen.getByText("向用户报告并发送APP集成清单")).toBeInTheDocument()
  })

  it("点击 header 后展开任务列表，再次点击折叠", async () => {
    const user = userEvent.setup()
    render(<TaskCard currentTaskTitle="向用户报告并发送APP集成清单" tasks={tasks} />)

    const toggle = screen.getByRole("button", { name: "切换任务列表" })
    await user.click(toggle)
    expect(screen.getByTestId("task-list")).toBeInTheDocument()
    expect(screen.getByText("提取核心信息和视频需求")).toBeInTheDocument()

    await user.click(toggle)
    expect(screen.queryByTestId("task-list")).toBeNull()
  })

  it("展示完成进度（completed/total）", () => {
    render(<TaskCard currentTaskTitle="x" tasks={tasks} />)
    expect(screen.getByText("2 / 3")).toBeInTheDocument()
  })

  it("已完成项展示绿色勾选图标", async () => {
    const user = userEvent.setup()
    render(<TaskCard currentTaskTitle="x" tasks={tasks} />)
    await user.click(screen.getByRole("button", { name: "切换任务列表" }))
    const checks = screen.getAllByTestId("task-check")
    expect(checks).toHaveLength(2)
  })
})
