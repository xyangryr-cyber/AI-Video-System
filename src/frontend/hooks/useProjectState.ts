import { useQuery } from "@tanstack/react-query"
import { apiClient } from "../api/client"
import type { ProjectState } from "../../shared/types/project_state"

export function useProjectState(projectId: string) {
  return useQuery({
    queryKey: ["project", projectId],
    queryFn: () => apiClient.get<ProjectState>(`/api/projects/${projectId}/state`),
    enabled: !!projectId,
  })
}
