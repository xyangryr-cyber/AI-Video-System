import type { ReactElement } from "react"

type Status = "ok" | "damaged" | "missing"
interface Props { status: Status; compact?: boolean }

const LABELS: Record<Status, string> = { ok: "", damaged: "damaged", missing: "missing" }

export function ArtifactStatusBadge({ status, compact = false }: Props): ReactElement | null {
  if (status === "ok") return null
  return (
    <span
      title={LABELS[status]}
      className="text-xs bg-red-100 text-red-700 px-1.5 py-0.5 rounded"
    >
      {compact ? "!" : LABELS[status]}
    </span>
  )
}
