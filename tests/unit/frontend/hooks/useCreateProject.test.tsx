import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { apiClient } from "@frontend/api/client";
import { createQueryClient } from "@frontend/lib/queryClient";
import { useCreateProject } from "@frontend/hooks/useCreateProject";

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

describe("useCreateProject", () => {
  it("mutationFn calls apiClient.post with correct args", async () => {
    vi.mocked(apiClient.post).mockResolvedValue({ id: "proj_new" });
    const { result } = renderHook(() => useCreateProject(), { wrapper: wrapper() });

    await act(async () => {
      await result.current.mutateAsync({ title: "Test", description: "Description text" });
    });

    expect(apiClient.post).toHaveBeenCalledWith("/api/projects", {
      title: "Test",
      description: "Description text",
    });
  });

  it("resolves with apiClient response on success", async () => {
    const mockResponse = { id: "proj_new", title: "Test" };
    vi.mocked(apiClient.post).mockResolvedValue(mockResponse);
    const { result } = renderHook(() => useCreateProject(), { wrapper: wrapper() });

    let data: unknown;
    await act(async () => {
      data = await result.current.mutateAsync({ title: "T", description: "Description text here" });
    });

    expect(data).toEqual(mockResponse);
  });

  it("exposes isPending=true during request", async () => {
    vi.mocked(apiClient.post).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ id: "x" }), 50)),
    );
    const { result } = renderHook(() => useCreateProject(), { wrapper: wrapper() });

    act(() => {
      result.current.mutate({ title: "T", description: "Description text here" });
    });

    await waitFor(() => expect(result.current.isPending).toBe(true));
  });

  it("exposes error on apiClient rejection", async () => {
    const apiError = { error_code: "SERVER_ERROR", message: "boom", status: 500 };
    vi.mocked(apiClient.post).mockRejectedValue(apiError);
    const { result } = renderHook(() => useCreateProject(), { wrapper: wrapper() });

    await act(async () => {
      try { await result.current.mutateAsync({ title: "T", description: "Description text here" }); } catch {}
    });

    await waitFor(() => {
      expect(result.current.error).not.toBeNull();
      expect(result.current.error).toEqual(apiError);
    });
  });
});
