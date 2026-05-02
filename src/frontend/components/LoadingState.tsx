import type { ReactElement } from "react"

export function LoadingState(): ReactElement {
  return <div data-testid="loading-state" className="p-6">加载中...</div>
}
