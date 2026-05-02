import { describe, it, expect, beforeEach } from "vitest";
import { useAppStore, resetAppStore } from "@frontend/store";

describe("app store", () => {
  beforeEach(() => resetAppStore());

  it("starts empty", () => {
    expect(useAppStore.getState().events).toEqual([]);
  });

  it("pushEvent appends", () => {
    useAppStore.getState().pushEvent({
      id: "e1", type: "phase.advanced", project_id: "p1",
      timestamp: "2026-04-17T10:00:00Z", payload: {},
    });
    expect(useAppStore.getState().events).toHaveLength(1);
    expect(useAppStore.getState().events[0].id).toBe("e1");
  });

  it("caps event buffer at 50", () => {
    for (let i = 0; i < 60; i++) {
      useAppStore.getState().pushEvent({
        id: `e${i}`, type: "x", project_id: "p",
        timestamp: "2026-04-17T10:00:00Z", payload: {},
      });
    }
    expect(useAppStore.getState().events).toHaveLength(50);
    expect(useAppStore.getState().events[0].id).toBe("e10");
  });
});
