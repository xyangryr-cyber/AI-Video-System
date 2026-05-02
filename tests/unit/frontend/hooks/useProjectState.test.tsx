import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { apiClient } from "@frontend/api/client";
import { createQueryClient } from "@frontend/lib/queryClient";
import { useProjectState } from "@frontend/hooks/useProjectState";
import stateProj001 from "../../../fixtures/api/projects/state_proj_001.json";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

function wrapper() {
  const qc = createQueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("useProjectState", () => {
  it("AC-1,AC-2 fetches ProjectState with all fields defined", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(stateProj001);
    const { result } = renderHook(() => useProjectState("proj_001"), { wrapper: wrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true), { timeout: 10000 });
    const s = result.current.data!;
    expect(s.project).toBeDefined();
    expect(s.phases).toBeDefined();
    expect(s.preferences).toBeDefined();
    expect(s.system_status).toBeDefined();
    expect(Array.isArray(s.phases)).toBe(true);
  });
});
