import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { BrandKit } from "@shared/types/brand_kit";
import type {
  SettingsResponse,
  PreferencesResponse,
  PreferencesUpdateRequest,
  SnapshotListResponse,
} from "@shared/types/settings";

export function useSettingsQuery() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: () => apiClient.get<SettingsResponse>("/api/settings"),
  });
}

export function useModelConfigMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: Record<string, unknown>) =>
      apiClient.put<{ ok: boolean }>("/api/settings/model-config", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] }),
  });
}

export function usePreferencesQuery() {
  return useQuery({
    queryKey: ["settings", "preferences"],
    queryFn: () =>
      apiClient.get<PreferencesResponse>("/api/settings/preferences"),
  });
}

export function usePreferencesMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: PreferencesUpdateRequest) =>
      apiClient.put<{ ok: boolean; snapshot_id: string }>(
        "/api/settings/preferences",
        data,
      ),
    onSuccess: () =>
      qc.invalidateQueries({ queryKey: ["settings", "preferences"] }),
  });
}

export function useBrandKitMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: BrandKit) =>
      apiClient.put<{ ok: boolean }>("/api/settings/brand-kit", data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings"] }),
  });
}

export function useSnapshotsQuery() {
  return useQuery({
    queryKey: ["settings", "preferences", "snapshots"],
    queryFn: () =>
      apiClient.get<SnapshotListResponse>(
        "/api/settings/preferences/snapshots",
      ),
  });
}

export function useRollbackMutation() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (snapshotId: string) =>
      apiClient.post<{ ok: boolean; new_snapshot_id: string }>(
        `/api/settings/preferences/snapshots/${snapshotId}/rollback`,
        {},
      ),
    onSuccess: () =>
      qc.invalidateQueries({
        queryKey: ["settings", "preferences", "snapshots"],
      }),
  });
}
