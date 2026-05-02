import { useState, useCallback } from "react"
import { apiClient } from "../api/client"
import type { ChatMessage } from "../components/workflow/mockData"

interface ChatResponse {
  project_id: string
  action: string
  response: string
  phase: number
  highlight_confirm_button?: boolean
  gate_satisfied?: boolean
  button_disabled_reason?: string | null
}

function ts(): string {
  return new Date().toLocaleTimeString("zh-CN", { hour: "2-digit", minute: "2-digit" })
}

export function useChat(projectId: string) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<{ message: string } | null>(null)
  const [highlightConfirm, setHighlightConfirm] = useState(false)
  const [gateSatisfied, setGateSatisfied] = useState(false)
  const [gateBlockedReason, setGateBlockedReason] = useState<string | null>(null)

  const sendMessage = useCallback(
    async (text: string) => {
      const trimmed = text.trim()
      if (!trimmed) return

      setError(null)

      const userMsg: ChatMessage = { role: "user", text: trimmed, ts: ts() }
      setMessages((prev) => [...prev, userMsg])
      setIsLoading(true)

      try {
        const res = await apiClient.post<ChatResponse>(
          `/api/projects/${projectId}/chat`,
          { message: trimmed, context: {} },
        )
        const agentMsg: ChatMessage = { role: "agent", text: res.response, ts: ts() }
        setMessages((prev) => [...prev, agentMsg])
        setHighlightConfirm(res.highlight_confirm_button ?? false)
        setGateSatisfied(res.gate_satisfied ?? false)
        setGateBlockedReason(res.button_disabled_reason ?? null)
      } catch (e: unknown) {
        const err = e as { message?: string }
        setError({ message: err.message ?? "发送失败，请重试" })
        throw e
      } finally {
        setIsLoading(false)
      }
    },
    [projectId],
  )

  return { messages, sendMessage, isLoading, error, highlightConfirm, gateSatisfied, gateBlockedReason }
}
