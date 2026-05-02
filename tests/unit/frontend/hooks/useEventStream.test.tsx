import { describe, it, expect, beforeEach, afterAll, vi } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Server } from "mock-socket";
import React from "react";
import { apiClient } from "@frontend/api/client";
import { createQueryClient } from "@frontend/lib/queryClient";
import { useEventStream } from "@frontend/hooks/useEventStream";
import eventsListResponse from "../../../fixtures/api/events/list_response.json";

const HOOK_WS_URL = "ws://localhost:8000/ws/proj_001/events/hook-test";

// Create mock-socket Server at module scope to intercept WebSocket connections.
const wsHookServer = new Server(HOOK_WS_URL);

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

afterAll(() => {
  wsHookServer.stop();
});

function wrapper({ children }: { children: React.ReactNode }) {
  const qc = createQueryClient();
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("useEventStream", () => {
  it("fetches history from REST on mount", async () => {
    vi.mocked(apiClient.get).mockResolvedValue(eventsListResponse);
    const { result } = renderHook(
      () => useEventStream("proj_001", HOOK_WS_URL),
      { wrapper }
    );
    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.events.length).toBeGreaterThanOrEqual(3);
    expect(result.current.events[0].id).toBe("e1");
  });
});
