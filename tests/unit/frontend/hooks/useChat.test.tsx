import { describe, it, expect, beforeEach, vi } from "vitest";
import { renderHook, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import { apiClient } from "@frontend/api/client";
import { createQueryClient } from "@frontend/lib/queryClient";
import { useChat } from "@frontend/hooks/useChat";

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

const mockChatResponse = {
  project_id: "proj_001",
  action: "clarify",
  response: "好的，已将时长调整为15分钟。",
  phase: 0,
  highlight_confirm_button: false,
  gate_satisfied: false,
  button_disabled_reason: null,
};

describe("useChat", () => {
  it("sendMessage appends user message optimistically", async () => {
    vi.mocked(apiClient.post).mockResolvedValue(mockChatResponse);
    const { result } = renderHook(() => useChat("proj_001"), { wrapper: wrapper() });

    await act(async () => {
      await result.current.sendMessage("把时长改成15分钟");
    });

    const userMsg = result.current.messages.find((m) => m.role === "user");
    expect(userMsg).toBeDefined();
    expect(userMsg!.text).toBe("把时长改成15分钟");
  });

  it("sendMessage calls apiClient.post with correct params", async () => {
    vi.mocked(apiClient.post).mockResolvedValue(mockChatResponse);
    const { result } = renderHook(() => useChat("proj_001"), { wrapper: wrapper() });

    await act(async () => {
      await result.current.sendMessage("把时长改成15分钟");
    });

    expect(apiClient.post).toHaveBeenCalledWith("/api/projects/proj_001/chat", {
      message: "把时长改成15分钟",
      context: {},
    });
  });

  it("appends agent response after API returns", async () => {
    vi.mocked(apiClient.post).mockResolvedValue(mockChatResponse);
    const { result } = renderHook(() => useChat("proj_001"), { wrapper: wrapper() });

    await act(async () => {
      await result.current.sendMessage("把时长改成15分钟");
    });

    const agentMsgs = result.current.messages.filter((m) => m.role === "agent");
    expect(agentMsgs).toHaveLength(1);
    expect(agentMsgs[0].text).toBe("好的，已将时长调整为15分钟。");
  });

  it("isLoading is true during request", async () => {
    vi.mocked(apiClient.post).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve(mockChatResponse), 50)),
    );
    const { result } = renderHook(() => useChat("proj_001"), { wrapper: wrapper() });

    act(() => {
      result.current.sendMessage("test");
    });

    await waitFor(() => expect(result.current.isLoading).toBe(true));
  });

  it("exposes error on API failure", async () => {
    const apiError = { error_code: "SERVER_ERROR", message: "服务器错误", status: 500 };
    vi.mocked(apiClient.post).mockRejectedValue(apiError);
    const { result } = renderHook(() => useChat("proj_001"), { wrapper: wrapper() });

    await act(async () => {
      try { await result.current.sendMessage("test"); } catch {}
    });

    expect(result.current.error).not.toBeNull();
  });
});
