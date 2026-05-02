import { useEffect, useRef } from "react"

export interface WebSocketOptions {
  onMessage?: (data: unknown) => void
  onOpen?: () => void
  onClose?: () => void
  enabled?: boolean
}

export function useWebSocket(url: string, opts: WebSocketOptions = {}): void {
  const { onMessage, onOpen, onClose, enabled = true } = opts
  const ref = useRef<WebSocket | null>(null)

  useEffect(() => {
    if (!enabled) return
    const ws = new WebSocket(url)
    ref.current = ws
    ws.onopen = () => onOpen?.()
    ws.onmessage = (e) => {
      try { onMessage?.(JSON.parse(e.data)) }
      catch { onMessage?.(e.data) }
    }
    ws.onclose = () => onClose?.()
    return () => { ws.close() }
  }, [url, enabled, onMessage, onOpen, onClose])
}
