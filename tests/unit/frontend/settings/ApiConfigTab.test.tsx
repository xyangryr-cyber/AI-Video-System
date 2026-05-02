import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { createQueryClient } from "@frontend/lib/queryClient";
import { ApiConfigTab } from "@frontend/components/settings/ApiConfigTab";
import { apiClient } from "@frontend/api/client";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

const mockModelConfig = {
  provider: "openai",
  model: "gpt-4",
  temperature: 0.7,
};

describe("ApiConfigTab", () => {
  it("AC-2 loads model config from GET /api/settings", async () => {
    let getCalled = false;
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.includes("/settings")) {
        getCalled = true;
        return { model_config_data: mockModelConfig, brand_kit: {} };
      }
      return {};
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <ApiConfigTab />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      const providerInput = screen.getByDisplayValue("openai");
      expect(providerInput).toBeInTheDocument();
    });
    expect(getCalled).toBe(true);
  });

  it("AC-2 saves model config via PUT /api/settings/model-config", async () => {
    let putBody: unknown = null;
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.includes("/settings")) return { model_config_data: mockModelConfig, brand_kit: {} };
      return {};
    });
    vi.mocked(apiClient.put).mockImplementation(async (_path: string, body: unknown) => {
      putBody = body;
      return { ok: true };
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <ApiConfigTab />
      </QueryClientProvider>,
    );

    await waitFor(() => expect(screen.getByDisplayValue("openai")).toBeInTheDocument());

    const input = screen.getByDisplayValue("openai");
    await userEvent.clear(input);
    await userEvent.type(input, "anthropic");

    await userEvent.click(screen.getByRole("button", { name: /保存配置/i }));

    await waitFor(() => {
      expect(putBody).toBeTruthy();
    });
    expect(putBody).toHaveProperty("provider");
  });
});
