import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { MemoryRouter } from "react-router-dom";
import { createQueryClient } from "@frontend/lib/queryClient";
import { SettingsPage } from "@frontend/pages/SettingsPage";
import { apiClient } from "@frontend/api/client";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("SettingsPage", () => {
  it("AC-1 renders sidebar with three Chinese tab labels", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.includes("/settings/preferences/snapshots")) return { snapshots: [] };
      if (path.includes("/settings/preferences")) return { global_rules_md: "", user_preferences_md: "" };
      if (path.includes("/settings")) return { model_config_data: {}, brand_kit: {} };
      return {};
    });
    vi.mocked(apiClient.put).mockResolvedValue({ ok: true });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    expect(screen.getByText("API 密钥配置")).toBeInTheDocument();
    expect(screen.getByText("模型与策略")).toBeInTheDocument();
    expect(screen.getByText("偏好全局快照")).toBeInTheDocument();
  });

  it("AC-1 clicking sidebar button switches active panel", async () => {
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.includes("/settings/preferences/snapshots")) return { snapshots: [] };
      if (path.includes("/settings/preferences")) return { global_rules_md: "", user_preferences_md: "" };
      if (path.includes("/settings")) return { model_config_data: {}, brand_kit: {} };
      return {};
    });
    vi.mocked(apiClient.put).mockResolvedValue({ ok: true });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );

    // Click 模型与策略 tab to show ModelsTab
    await userEvent.click(screen.getByText("模型与策略"));
    expect(screen.getByTestId("models-tab")).toBeInTheDocument();

    // Click 偏好全局快照 tab to show PreferencesTab
    await userEvent.click(screen.getByText("偏好全局快照"));
    expect(screen.getByTestId("preferences-tab")).toBeInTheDocument();

    // Click API 密钥配置 tab to show ApiConfigTab
    await userEvent.click(screen.getByText("API 密钥配置"));
    expect(screen.getByTestId("api-config-tab")).toBeInTheDocument();
  });
});
