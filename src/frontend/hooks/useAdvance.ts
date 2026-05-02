import { useMutation } from "@tanstack/react-query"
import { apiClient } from "../api/client"

interface AdvanceResponse {
  status: string
  current_phase: number
  from_phase?: number | null
  error_code?: string
}

export function useAdvance(projectId: string) {
  const mutation = useMutation({
    mutationFn: () =>
      apiClient.post<AdvanceResponse>(`/api/projects/${projectId}/advance`, undefined),
    retry: 0,
  })

  return {
    advance: mutation.mutateAsync,
    isAdvancing: mutation.isPending,
    error: mutation.error,
  }
}
