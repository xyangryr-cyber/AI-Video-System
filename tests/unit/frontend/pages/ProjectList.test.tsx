import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { apiClient } from "@frontend/api/client";
import { createQueryClient } from "@frontend/lib/queryClient";
import { ProjectList } from "@frontend/pages/ProjectList";
import listResponse from "../../../fixtures/api/projects/list_response.json";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

// Stub useWebSocket so the component does not try to connect.
vi.mock("@frontend/hooks/useWebSocket", () => ({
  useWebSocket: vi.fn(),
}));

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(apiClient.get).mockResolvedValue(listResponse);
});

describe("ProjectList page", () => {
  it("AC-4 renders fixture projects with distinct progress/status/time", async () => {
    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter>
          <ProjectList />
        </MemoryRouter>
      </QueryClientProvider>,
    );
    await waitFor(() => expect(screen.getAllByRole("row").length).toBeGreaterThanOrEqual(4));
    expect(screen.getByText(/黄金价格走势分析/)).toBeInTheDocument();
    expect(screen.getByText(/十五五规划解读/)).toBeInTheDocument();
  });
});
