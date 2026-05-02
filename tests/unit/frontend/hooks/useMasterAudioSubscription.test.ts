import { describe, it, expect, vi } from "vitest";
import { renderHook, act } from "@testing-library/react";
import { useMasterAudioSubscription } from "@frontend/hooks/useMasterAudioSubscription";
import { Server } from "mock-socket";

const WS_URL = "ws://localhost:8001/ws/projects/proj_1";

describe("useMasterAudioSubscription", () => {
  describe("AC-3: WS master_audio.updated event", () => {
    it("invokes onUpdate callback when master_audio.updated event arrives", async () => {
      const mockServer = new Server(WS_URL);
      try {
        const onUpdate = vi.fn();

        const { result, unmount } = renderHook(() =>
          useMasterAudioSubscription({
            projectId: "proj_1",
            enabled: true,
            onUpdate,
            getWsUrl: () => WS_URL,
          }),
        );

        // Wait for connection to be established
        await vi.waitFor(() => expect(mockServer.clients().length).toBe(1));

        // Simulate master_audio.updated event
        act(() => {
          mockServer.emit("message", JSON.stringify({
            type: "master_audio.updated",
            payload: { phase: 4, version: 2 },
          }));
        });

        await vi.waitFor(() => expect(onUpdate).toHaveBeenCalledOnce());
        expect(result.current.loading).toBe(false);

        unmount();
      } finally {
        mockServer.stop();
      }
    });

    it("does not connect when enabled=false", () => {
      const mockServer = new Server(WS_URL);
      try {
        const onUpdate = vi.fn();
        renderHook(() =>
          useMasterAudioSubscription({
            projectId: "proj_1",
            enabled: false,
            onUpdate,
            getWsUrl: () => WS_URL,
          }),
        );
        expect(mockServer.clients().length).toBe(0);
      } finally {
        mockServer.stop();
      }
    });

    it("handles non-json messages gracefully", async () => {
      const mockServer = new Server("ws://localhost:8002/ws/projects/proj_1");
      try {
        const onUpdate = vi.fn();
        const { unmount } = renderHook(() =>
          useMasterAudioSubscription({
            projectId: "proj_1",
            enabled: true,
            onUpdate,
            getWsUrl: () => "ws://localhost:8002/ws/projects/proj_1",
          }),
        );

        await vi.waitFor(() => expect(mockServer.clients().length).toBe(1));

        act(() => {
          mockServer.emit("message", "not-valid-json{{{");
        });

        // Give time to process, onUpdate should not be called
        await new Promise((r) => setTimeout(r, 100));
        expect(onUpdate).not.toHaveBeenCalled();

        unmount();
      } finally {
        mockServer.stop();
      }
    });
  });
});
