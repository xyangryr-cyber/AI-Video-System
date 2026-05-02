import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";

export function useArtifact(projectId: string, phase: number) {
  return useQuery({
    queryKey: ["artifact", projectId, phase],
    queryFn: async () => {
      const resp = await apiClient.get<{ artifact_data?: Record<string, unknown> | null }>(
        `/api/projects/${projectId}/phases/${phase}/artifact`,
      );
      return resp.artifact_data ?? null;
    },
    enabled: !!projectId && phase >= 0,
  });
}
