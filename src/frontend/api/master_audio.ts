import { apiClient } from "@frontend/api/client";
import type { GetMasterAudioResponse } from "@shared/types/api_master_audio";

export function fetchMasterAudio(
  projectId: string,
  phase: 4 | 5 | 6 = 4,
): Promise<GetMasterAudioResponse> {
  return apiClient.get<GetMasterAudioResponse>(
    `/api/projects/${projectId}/artifacts/master_audio?phase=${phase}`,
  );
}
