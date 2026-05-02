import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { apiClient } from "@frontend/api/client";
import { createQueryClient } from "@frontend/lib/queryClient";
import { useProjects } from "@frontend/hooks/useProjects";
import listResponse from "../../../fixtures/api/projects/list_response.json";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

// Stub out useWebSocket to intercept WS messages for test verification.
// The WS cache-invalidation behavior is verified via the captured callback.
let capturedOnMessage: ((data: unknown) => void) | undefined;

vi.mock("@frontend/hooks/useWebSocket", () => ({
  useWebSocket: (_url: string, opts: { onMessage?: (d: unknown) => void; enabled?: boolean }) => {
    if (opts.onMessage) capturedOnMessage = opts.onMessage;
  },
}));

beforeEach(() => {
  vi.clearAllMocks();
  capturedOnMessage = undefined;
});

function wrapper(qc = createQueryClient()) {
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("useProjects", () => {
  it("returns fixture-backed project list", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(listResponse);
    const { result } = renderHook(() => useProjects(), { wrapper: wrapper() });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data!.length).toBeGreaterThan(0);
    expect(result.current.data![0]).toHaveProperty("latest_reached_phase");
  });

  it("AC-5: WS phase.advanced event invalidates cache within 6s", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(listResponse);
    const qc = createQueryClient();
    const { result } = renderHook(() => useProjects("ws://localhost:8000/ws/projects"), {
      wrapper: wrapper(qc),
    });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(capturedOnMessage).toBeDefined();

    const t0 = performance.now();
    act(() => {
      capturedOnMessage!({
        type: "phase.advanced", project_id: "proj_001",
        timestamp: new Date().toISOString(), payload: { phase: 5 },
      });
    });
    await waitFor(() => {
      expect(qc.getQueryState(["projects"])?.dataUpdateCount).toBeGreaterThan(1);
    }, { timeout: 6000 });
    const elapsed = performance.now() - t0;
    expect(elapsed).toBeLessThan(6000);
  });
});
