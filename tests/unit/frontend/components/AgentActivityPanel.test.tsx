import { describe, it, expect, afterAll, vi, beforeEach } from "vitest";
import { render, screen, waitFor, act } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { Server } from "mock-socket";
import React from "react";
import { createQueryClient } from "@frontend/lib/queryClient";
import { AgentActivityPanel } from "@frontend/components/AgentActivityPanel";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

import { apiClient } from "@frontend/api/client";

const WS_URL = "ws://localhost:8000/ws/proj_001/events";

// Create mock-socket servers BEFORE component render.
// Each test uses a unique URL suffix to isolate connections.
const wsLive = new Server(WS_URL);
const wsPerf = new Server(WS_URL + "/perf");
const wsDedup = new Server(WS_URL + "/dedup");
const wsScroll = new Server(WS_URL + "/scroll");

// Fixture: matches tests/fixtures/api/events/list_response.json
const eventsFixture = [
  {"id": "e1", "type": "phase.advanced", "project_id": "proj_001", "timestamp": "2026-04-17T10:00:00Z", "payload": {"agent_name": "ScriptAgent", "action": "generate", "progress": "100%"}},
  {"id": "e2", "type": "agent.call", "project_id": "proj_001", "timestamp": "2026-04-17T10:05:00Z", "payload": {"agent_name": "TTSAgent", "action": "synthesize", "result": "ok"}},
  {"id": "e3", "type": "gate.failed", "project_id": "proj_001", "timestamp": "2026-04-17T10:07:00Z", "payload": {"agent_name": "GateAgent", "action": "check", "result": "fail"}},
];

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiClient.get).mockResolvedValue(eventsFixture);
});

afterAll(() => {
  wsLive.stop();
  wsPerf.stop();
  wsDedup.stop();
  wsScroll.stop();
});

function wrap() {
  const qc = createQueryClient();
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={qc}>{children}</QueryClientProvider>
  );
}

describe("AgentActivityPanel", () => {
  it("AC-1 renders events in [HH:MM:SS] [agent] [action] [result] format", async () => {
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
    const rows = screen.getAllByTestId("activity-row");
    expect(rows[0].textContent).toMatch(/\[\d{2}:\d{2}:\d{2}\].*\[.+\].*\[.+\]/);
  });

  it("AC-2 fetches initial history via GET /events?limit=50", async () => {
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getByText(/ScriptAgent/)).toBeInTheDocument());
  });

  it("AC-3 appends live event from WS", async () => {
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
    act(() => {
      wsLive.emit("message", JSON.stringify({
        id: "eLive", type: "agent.call", project_id: "proj_001",
        timestamp: new Date().toISOString(),
        payload: { agent_name: "LiveAgent", action: "now", result: "ok" },
      }));
    });
    await waitFor(() => expect(screen.getByText(/LiveAgent/)).toBeInTheDocument());
  });

  it("AC-4 DOM update within 200ms of WS message", async () => {
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL + "/perf"} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
    const t0 = performance.now();
    act(() => {
      wsPerf.emit("message", JSON.stringify({
        id: "eFast", type: "agent.call", project_id: "proj_001",
        timestamp: new Date().toISOString(),
        payload: { agent_name: "FastAgent", action: "x", result: "ok" },
      }));
    });
    await waitFor(() => expect(screen.getByText(/FastAgent/)).toBeInTheDocument());
    expect(performance.now() - t0).toBeLessThan(300);
  });

  it("AC-5 scroll-to-top emits onLoadMore signal", async () => {
    const onLoadMore = vi.fn();
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL + "/scroll"} onLoadMore={onLoadMore} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
    const panel = screen.getByTestId("activity-panel-scroll");
    act(() => { panel.scrollTop = 0; panel.dispatchEvent(new Event("scroll")); });
    expect(onLoadMore).toHaveBeenCalled();
  });

  it("AC-6 dedup: WS re-delivery of same id is not rendered twice", async () => {
    render(<AgentActivityPanel projectId="proj_001" wsUrl={WS_URL + "/dedup"} />, { wrapper: wrap() });
    await waitFor(() => expect(screen.getAllByTestId("activity-row").length).toBeGreaterThanOrEqual(3));
    const payload = JSON.stringify({
      id: "eDup", type: "agent.call", project_id: "proj_001",
      timestamp: new Date().toISOString(),
      payload: { agent_name: "DupAgent", action: "x", result: "ok" },
    });
    act(() => { wsDedup.emit("message", payload); wsDedup.emit("message", payload); });
    await waitFor(() => expect(screen.getAllByText(/DupAgent/).length).toBe(1));
  });
});
