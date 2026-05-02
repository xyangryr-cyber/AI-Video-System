import type { ChangeEvent, KeyboardEvent, ReactElement } from "react"
import { useState } from "react"
import { ArrowUp } from "lucide-react"

interface ChatInputProps {
  onSend?: (text: string) => void
  placeholder?: string
  disabled?: boolean
}

export function ChatInput({
  onSend,
  placeholder = "发送消息给 Agent",
  disabled = false,
}: ChatInputProps): ReactElement {
  const [value, setValue] = useState("")

  const handleSend = () => {
    const trimmed = value.trim()
    if (!trimmed) return
    onSend?.(trimmed)
    setValue("")
  }

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div
      data-testid="chat-input"
      className="bg-slate-50 border border-slate-200 rounded-3xl flex flex-col pt-4 pb-3 px-4 relative transition-colors focus-within:border-blue-400 focus-within:bg-white shadow-sm"
    >
      <textarea
        className="w-full bg-transparent text-slate-800 px-2 text-[15px] focus:outline-none resize-none placeholder-slate-400 min-h-[40px]"
        rows={1}
        placeholder={placeholder}
        value={value}
        aria-label="消息输入框"
        onChange={(e: ChangeEvent<HTMLTextAreaElement>) => setValue(e.target.value)}
        onKeyDown={handleKeyDown}
      />
      <div className="flex justify-end items-center mt-2 px-1">
        <button
          type="button"
          aria-label="发送消息"
          onClick={handleSend}
          className="w-9 h-9 rounded-full bg-[#1e293b] flex items-center justify-center hover:bg-black transition-colors text-white shadow-md disabled:opacity-50"
          disabled={disabled || !value.trim()}
        >
          <ArrowUp className="w-5 h-5" />
        </button>
      </div>
    </div>
  )
}
