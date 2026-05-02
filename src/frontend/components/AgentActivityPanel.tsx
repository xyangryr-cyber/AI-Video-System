import type { ReactElement, UIEvent } from "react"
import { useEventStream } from "../hooks/useEventStream"
import { ActivityEventRow } from "./ActivityEventRow"

interface Props {
  projectId: string
  wsUrl: string
  onLoadMore?: () => void
}

export function AgentActivityPanel({ projectId, wsUrl, onLoadMore }: Props): ReactElement {
  const { events, isLoading } = useEventStream(projectId, wsUrl)
  if (isLoading) return <div>加载事件...</div>

  function handleScroll(e: UIEvent<HTMLDivElement>) {
    if (e.currentTarget.scrollTop === 0) {
      onLoadMore?.()
    }
  }

  return (
    <div className="border rounded p-3 max-h-[400px] overflow-y-auto">
      <div className="text-sm font-semibold mb-2">Agent 活动</div>
      <div
        data-testid="activity-panel-scroll"
        className="overflow-y-auto"
        onScroll={handleScroll}
      >
        {events.map((e) => <ActivityEventRow key={e.id} event={e} />)}
      </div>
    </div>
  )
}
