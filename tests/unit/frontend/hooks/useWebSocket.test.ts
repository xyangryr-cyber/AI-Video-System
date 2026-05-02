import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { Server } from "mock-socket";
import { useWebSocket } from "@frontend/hooks/useWebSocket";

describe("useWebSocket", () => {
  let mockServer: Server;
  const URL = "ws://localhost:8000/ws/proj_001";

  beforeEach(() => { mockServer = new Server(URL); });
  afterEach(() => { mockServer.stop(); });

  it("receives messages and calls onMessage", async () => {
    const onMessage = vi.fn();
    const { unmount } = renderHook(() => useWebSocket(URL, { onMessage }));
    await vi.waitFor(() => expect(mockServer.clients().length).toBe(1));
    act(() => { mockServer.emit("message", JSON.stringify({ type: "phase.advanced" })); });
    await vi.waitFor(() => expect(onMessage).toHaveBeenCalledOnce());
    expect(onMessage.mock.calls[0][0]).toMatchObject({ type: "phase.advanced" });
    unmount();
  });

  it("skips when enabled=false", () => {
    const onMessage = vi.fn();
    renderHook(() => useWebSocket(URL, { onMessage, enabled: false }));
    expect(mockServer.clients().length).toBe(0);
  });
});
