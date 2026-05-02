import { describe, it, expect, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

vi.mock("@frontend/hooks/useSettings", () => ({
  useSettingsQuery: () => ({
    data: { model_config_data: { provider: "gemini", temperature: "0.7" } },
    isLoading: false,
  }),
  useModelConfigMutation: () => ({ mutate: vi.fn(), isPending: false }),
  usePreferencesQuery: () => ({
    data: { global_rules_md: "rule 1", user_preferences_md: "pref 1" },
    isLoading: false,
  }),
  usePreferencesMutation: () => ({ mutate: vi.fn(), isPending: false }),
  useBrandKitMutation: () => ({ mutate: vi.fn(), isPending: false }),
}));

import { SettingsPage } from "@frontend/pages/SettingsPage";

describe("SettingsPage visual alignment", () => {
  function renderPage() {
    const qc = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return render(
      <QueryClientProvider client={qc}>
        <MemoryRouter>
          <SettingsPage />
        </MemoryRouter>
      </QueryClientProvider>,
    );
  }

  it("renders '系统设置' heading", () => {
    renderPage();
    expect(screen.getByText("系统设置")).toBeDefined();
  });

  it("renders sidebar with Chinese tab labels", () => {
    renderPage();
    expect(screen.getByText("API 密钥配置")).toBeDefined();
    expect(screen.getByText("模型与策略")).toBeDefined();
    expect(screen.getByText("偏好全局快照")).toBeDefined();
  });

  it("renders content card with rounded-2xl", () => {
    renderPage();
    const cards = document.querySelectorAll(".rounded-2xl");
    expect(cards.length).toBeGreaterThan(0);
  });

  it("ApiConfigTab renders 'API 密钥配置 (全局)' header", () => {
    renderPage();
    expect(screen.getByText("API 密钥配置 (全局)")).toBeDefined();
  });

  it("ApiConfigTab renders '保存配置' button", () => {
    renderPage();
    expect(screen.getByText("保存配置")).toBeDefined();
  });
});
