import type { ReactElement } from "react"
import { TechnicalDetails } from "./TechnicalDetails"
import type { ErrorTier } from "../../types/errors"

interface Props {
  code: string
  message: string
  actions: string[]
  tier: ErrorTier
  details?: unknown
  onAction: (action: string) => void
  onClose: () => void
}

export function ErrorModal({ code, message, actions, tier, details, onAction, onClose }: Props): ReactElement {
  const isDanger = tier === "user_action"
  const panelClass = isDanger
    ? "bg-white rounded-lg p-6 max-w-md w-full space-y-4 border-2 border-red-500"
    : "bg-white rounded-lg p-6 max-w-md w-full space-y-4"
  return (
    <div role="dialog" className="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
      <div className={panelClass} data-tier={tier}>
        <div>
          <div className="font-mono text-xs text-gray-500">{code}</div>
          <div className={isDanger ? "text-lg font-semibold text-red-600" : "text-lg font-semibold"}>{message}</div>
        </div>
        {tier === "user_action" && details !== undefined && <TechnicalDetails details={details} />}
        <div className="flex gap-2 justify-end">
          {actions.map((a) => (
            <button
              key={a} className="px-3 py-1 border rounded hover:bg-gray-50"
              onClick={() => onAction(a)}
            >{a}</button>
          ))}
          <button className="px-3 py-1 text-gray-500" onClick={onClose}>关闭</button>
        </div>
      </div>
    </div>
  )
}
