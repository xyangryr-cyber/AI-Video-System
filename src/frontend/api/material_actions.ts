import { apiClient } from "@frontend/api/client";

export interface SupplementMaterialRequest {
  shot_id: string;
  material_type: string;
  description: string;
}

export interface SupplementMaterialResponse {
  task_id: string;
  material_id: string;
}

export function supplementMaterial(
  projectId: string,
  payload: SupplementMaterialRequest,
): Promise<SupplementMaterialResponse> {
  return apiClient.post<SupplementMaterialResponse>(
    `/api/projects/${projectId}/materials/supplement`,
    payload,
  );
}
