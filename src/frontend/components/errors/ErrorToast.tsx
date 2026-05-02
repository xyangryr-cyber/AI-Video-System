import type { ReactElement } from "react"

interface Props { code: string; message: string; etaSec?: number }

export function ErrorToast({ code, message, etaSec }: Props): ReactElement {
  return (
    <div className="fixed bottom-4 right-4 bg-yellow-100 border border-yellow-400 text-yellow-800 px-4 py-2 rounded shadow">
      <div className="font-mono text-xs">{code}</div>
      <div className="text-sm">{message}</div>
      {etaSec !== undefined && <div className="text-xs opacity-70">自动重试中 (ETA {etaSec}s)</div>}
    </div>
  )
}
