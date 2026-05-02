import type { PhaseState } from "../../shared/types/project_state";

export function useArtifactStatus(
  phases: PhaseState[] | undefined,
  phase: number,
): "ok" | "damaged" | "missing" {
  const p = phases?.find((x) => x.phase_num === phase);
  return (p?.artifact_status as "ok" | "damaged" | "missing") ?? "ok";
}
