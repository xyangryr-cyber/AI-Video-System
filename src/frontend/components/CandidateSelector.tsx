import { useMemo } from "react";
import type { ReactElement } from "react";
import { toast } from "sonner";
import { apiClient } from "../api/client";
import { CandidateCard } from "./CandidateCard";
import { useCandidateSelection } from "../hooks/useCandidateSelection";
import type { CandidateLike } from "../types/candidates";

interface Props<T extends CandidateLike> {
  projectId: string;
  phase: number;
  candidates: T[];
}

const REMINDER_MSG = "已等待 60 秒，请选择一个候选方案，或点击「跳过并接受推荐」";

export function CandidateSelector<T extends CandidateLike>({
  projectId,
  phase,
  candidates,
}: Props<T>): ReactElement {
  const visible = useMemo(() => candidates.slice(0, 3), [candidates]);
  const sel = useCandidateSelection(
    visible,
    async (candidateId) => {
      await apiClient.post(`/api/projects/${projectId}/preferences/confirm`, {
        phase,
        decisions: {
          candidate_id: candidateId,
          action: candidateId === visible.find((c) => c.is_recommended)?.id ? "accept" : "select",
        },
      });
    },
    { onReminder: () => toast(REMINDER_MSG), reminderMs: 60_000 },
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
        {visible.map((c) => (
          <CandidateCard
            key={c.id}
            candidate={c}
            isActive={sel.selectedId === c.id}
            onPreview={() => sel.preview(c.id)}
            onSelect={() => sel.select(c.id)}
          />
        ))}
      </div>
      <div className="flex gap-2">
        <button
          className="px-3 py-1 border rounded"
          disabled={sel.state !== "selected"}
          onClick={sel.confirm}
        >
          确认
        </button>
        <button className="px-3 py-1 border rounded" onClick={sel.skipAndAccept}>
          跳过并接受推荐
        </button>
      </div>
    </div>
  );
}
