import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import { useWebSocket } from "./useWebSocket";
import type { ProjectListItem } from "../types/project";

const REFRESH_EVENTS = new Set(["phase.advanced", "status.changed", "project.updated"]);

export function useProjects(wsUrl?: string) {
  const qc = useQueryClient();
  const query = useQuery({
    queryKey: ["projects"],
    queryFn: () => apiClient.get<ProjectListItem[]>("/api/projects"),
  });

  useWebSocket(wsUrl ?? "", {
    enabled: !!wsUrl,
    onMessage: (data) => {
      const evt = data as { type?: string };
      if (evt?.type && REFRESH_EVENTS.has(evt.type)) {
        qc.invalidateQueries({ queryKey: ["projects"] });
      }
    },
  });

  return query;
}
