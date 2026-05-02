import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { apiClient } from "@frontend/api/client";
import { createQueryClient } from "@frontend/lib/queryClient";
import { useAdvance } from "@frontend/hooks/useAdvance";

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

const mockAdvanceResponse = {
  status: "advanced",
  current_phase: 1,
  from_phase: 0,
};

describe("useAdvance", () => {
  it("advance calls apiClient.post with correct path", async () => {
    vi.mocked(apiClient.post).mockResolvedValue(mockAdvanceResponse);
    const { result } = renderHook(() => useAdvance("proj_001"), { wrapper: wrapper() });

    await act(async () => {
      await result.current.advance();
    });

    expect(apiClient.post).toHaveBeenCalledWith("/api/projects/proj_001/advance", undefined);
  });

  it("resolves with response on success", async () => {
    vi.mocked(apiClient.post).mockResolvedValue(mockAdvanceResponse);
    const { result } = renderHook(() => useAdvance("proj_001"), { wrapper: wrapper() });

    let data: unknown;
    await act(async () => {
      data = await result.current.advance();
    });

    expect(data).toEqual(mockAdvanceResponse);
  });

  it("isAdvancing is true during request", async () => {
    vi.mocked(apiClient.post).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockAdvanceResponse), 50)),
    );
    const { result } = renderHook(() => useAdvance("proj_001"), { wrapper: wrapper() });

    act(() => {
      result.current.advance();
    });

    await waitFor(() => expect(result.current.isAdvancing).toBe(true));
  });

  it("exposes error on API failure", async () => {
    const apiError = { error_code: "GATE_FAILED", message: "门禁未通过", status: 422 };
    vi.mocked(apiClient.post).mockRejectedValue(apiError);
    const { result } = renderHook(() => useAdvance("proj_001"), { wrapper: wrapper() });

    await act(async () => {
      try { await result.current.advance(); } catch {}
    });

    await waitFor(() => expect(result.current.error).not.toBeNull());
  });
});
