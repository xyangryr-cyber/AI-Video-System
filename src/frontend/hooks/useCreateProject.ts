import { useMutation } from "@tanstack/react-query";
import { apiClient } from "../api/client";
import type { ProjectListItem } from "../types/project";

export interface CreateProjectInput {
  title: string;
  description: string;
}

const CREATE_TIMEOUT_MS = 30_000;

function timeout(ms: number): Promise<never> {
  return new Promise((_, reject) =>
    setTimeout(() => reject(new Error("请求超时，请检查网络后重试")), ms),
  );
}

export function useCreateProject() {
  return useMutation({
    mutationFn: (input: CreateProjectInput) =>
      Promise.race([
        apiClient.post<ProjectListItem>("/api/projects", input),
        timeout(CREATE_TIMEOUT_MS),
      ]),
    retry: 0,
  });
}
