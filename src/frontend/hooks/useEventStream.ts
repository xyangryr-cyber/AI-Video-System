import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useWebSocket } from "./useWebSocket";
import type { AgentEvent } from "../types/events";

const LIMIT = 50;

export function useEventStream(projectId: string, wsUrl: string) {
  const history = useQuery({
    queryKey: ["events", projectId],
    queryFn: () => apiClient.get<AgentEvent[]>(`/api/projects/${projectId}/events?limit=${LIMIT}`),
    enabled: !!projectId,
  });
  const [live, setLive] = useState<AgentEvent[]>([]);
  useWebSocket(wsUrl, {
    enabled: !!wsUrl,
    onMessage: (data) => {
      const evt = data as AgentEvent;
      if (!evt?.id) return;
      setLive((prev) => (prev.some((e) => e.id === evt.id) ? prev : [...prev, evt]));
    },
  });
  const merged = useMemo(() => {
    const seen = new Set<string>();
    const all = [...(history.data ?? []), ...live];
    const uniq: AgentEvent[] = [];
    for (const e of all) {
      if (seen.has(e.id)) continue;
      seen.add(e.id);
      uniq.push(e);
    }
    return uniq.slice(-LIMIT);
  }, [history.data, live]);
  return { events: merged, isLoading: history.isLoading, isError: history.isError };
}
