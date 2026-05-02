import type { ReactElement } from "react"
import type { CandidateLike } from "../types/candidates"

interface Props<T extends CandidateLike> {
  candidate: T
  isActive: boolean
  onPreview: () => void
  onSelect: () => void
}

export function CandidateCard<T extends CandidateLike>({ candidate, isActive, onPreview, onSelect }: Props<T>): ReactElement {
  return (
    <div
      data-testid="candidate-card"
      className={`border rounded p-3 cursor-pointer ${isActive ? "ring-2 ring-blue-500" : ""}`}
      onClick={onPreview}
    >
      {candidate.preview_url && <div className="h-20 bg-gray-100 mb-2" />}
      <div className="text-sm">
        {candidate.id}
        {candidate.is_recommended && <span className="ml-2 text-xs text-blue-600">推荐</span>}
      </div>
      <button
        className="mt-2 px-2 py-1 text-xs border rounded"
        onClick={(e) => { e.stopPropagation(); onSelect() }}
      >选择</button>
    </div>
  )
}
