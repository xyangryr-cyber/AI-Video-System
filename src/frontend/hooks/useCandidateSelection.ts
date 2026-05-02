import { useEffect, useRef, useState } from "react";
import type { CandidateLike, CandidateState } from "../types/candidates";

interface Options {
  onReminder?: () => void;
  reminderMs?: number;
}

export function useCandidateSelection<T extends CandidateLike>(
  candidates: T[],
  onConfirm: (candidateId: string) => void,
  opts: Options = {},
) {
  const { onReminder, reminderMs = 60_000 } = opts;
  const [state, setState] = useState<CandidateState>("idle");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const reminderFired = useRef(false);

  useEffect(() => {
    if (state !== "idle" || reminderFired.current || !onReminder) return;
    const t = setTimeout(() => {
      reminderFired.current = true;
      onReminder();
    }, reminderMs);
    return () => clearTimeout(t);
  }, [state, onReminder, reminderMs]);

  return {
    state,
    selectedId,
    preview(id: string) {
      setSelectedId(id);
      setState("previewing");
    },
    select(id: string) {
      setSelectedId(id);
      setState("selected");
    },
    confirm() {
      if (state !== "selected" || !selectedId) return;
      setState("confirmed");
      onConfirm(selectedId);
    },
    skipAndAccept() {
      const rec = candidates.find((c) => c.is_recommended) ?? candidates[0];
      if (!rec) return;
      setSelectedId(rec.id);
      setState("confirmed");
      onConfirm(rec.id);
    },
  };
}
