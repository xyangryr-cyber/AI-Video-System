import { describe, it, expect, vi } from "vitest"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { ChatInput } from "@frontend/components/workflow/ChatInput"

describe("ChatInput", () => {
  it("默认发送按钮禁用（空输入）", () => {
    render(<ChatInput />)
    const send = screen.getByRole("button", { name: "发送消息" })
    expect(send).toBeDisabled()
  })

  it("点击发送按钮触发 onSend(text) 并清空输入", async () => {
    const user = userEvent.setup()
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)

    const textarea = screen.getByLabelText("消息输入框") as HTMLTextAreaElement
    await user.type(textarea, "hello world")
    await user.click(screen.getByRole("button", { name: "发送消息" }))

    expect(onSend).toHaveBeenCalledWith("hello world")
    expect(textarea.value).toBe("")
  })

  it("Enter 键发送（无 Shift）；Shift+Enter 不发送", async () => {
    const user = userEvent.setup()
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)
    const textarea = screen.getByLabelText("消息输入框") as HTMLTextAreaElement

    await user.type(textarea, "ping")
    await user.keyboard("{Enter}")
    expect(onSend).toHaveBeenCalledWith("ping")

    onSend.mockClear()
    await user.type(textarea, "newline")
    await user.keyboard("{Shift>}{Enter}{/Shift}")
    expect(onSend).not.toHaveBeenCalled()
  })

  it("不发送纯空白消息", async () => {
    const user = userEvent.setup()
    const onSend = vi.fn()
    render(<ChatInput onSend={onSend} />)
    const textarea = screen.getByLabelText("消息输入框") as HTMLTextAreaElement
    await user.type(textarea, "   ")
    await user.keyboard("{Enter}")
    expect(onSend).not.toHaveBeenCalled()
  })

  it("容器使用 focus-within:border-blue-400 类（视觉聚焦高亮）", () => {
    render(<ChatInput />)
    const container = screen.getByTestId("chat-input")
    expect(container.className).toContain("focus-within:border-blue-400")
  })
})
