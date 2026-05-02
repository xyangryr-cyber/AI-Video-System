import type { ReactElement } from "react"
import type { AgentEvent } from "../types/events"

interface Props { event: AgentEvent }

export function ActivityEventRow({ event }: Props): ReactElement {
  const ts = new Date(event.timestamp)
  const hhmmss = ts.toTimeString().slice(0, 8)
  const agent = event.payload?.agent_name ?? "-"
  const action = event.payload?.action ?? event.type
  const result = event.payload?.result ?? event.payload?.progress ?? ""
  return (
    <div data-testid="activity-row" className="text-xs font-mono py-0.5">
      [{hhmmss}] [{agent}] [{action}] [{result}]
    </div>
  )
}
