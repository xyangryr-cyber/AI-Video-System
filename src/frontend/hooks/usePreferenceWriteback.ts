import { useCallback, useEffect, useState } from "react";
import type { WritebackSuggestion } from "../components/PreferenceWritebackCard";
import { apiClient } from "../api/client";

interface UsePreferenceWritebackOptions {
  projectId: string;
}

interface UsePreferenceWritebackReturn {
  suggestions: WritebackSuggestion[];
  loading: boolean;
  error: string | null;
  fetchSuggestions: () => Promise<void>;
  saveSelected: (selectedIds: string[]) => Promise<void>;
}

export function usePreferenceWriteback({
  projectId,
}: UsePreferenceWritebackOptions): UsePreferenceWritebackReturn {
  const [suggestions, setSuggestions] = useState<WritebackSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSuggestions = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await apiClient.get<{ suggestions: WritebackSuggestion[] }>(
        `/api/projects/${projectId}/preferences/writeback-suggestions`,
      );
      setSuggestions(res.suggestions ?? []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to fetch suggestions");
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const saveSelected = useCallback(
    async (selectedIds: string[]) => {
      setLoading(true);
      setError(null);
      try {
        await apiClient.post(
          `/api/projects/${projectId}/preferences/stage`,
          { suggestion_ids: selectedIds },
        );
        setSuggestions((prev) =>
          prev.filter((s) => !selectedIds.includes(s.id)),
        );
      } catch (e) {
        setError(e instanceof Error ? e.message : "Failed to save preferences");
      } finally {
        setLoading(false);
      }
    },
    [projectId],
  );

  // Auto-fetch on mount
  useEffect(() => {
    fetchSuggestions();
  }, [fetchSuggestions]);

  return { suggestions, loading, error, fetchSuggestions, saveSelected };
}
