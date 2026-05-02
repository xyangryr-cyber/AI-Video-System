import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { createQueryClient } from "@frontend/lib/queryClient";
import { PreferencesTab } from "@frontend/components/settings/PreferencesTab";
import { apiClient } from "@frontend/api/client";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

const mockPreferences = {
  global_rules_md: "# Rules\n- Use formal tone",
  user_preferences_md: "# Preferences\n- Duration: 3min",
};

describe("PreferencesTab", () => {
  it("AC-3 loads preferences from GET /api/settings/preferences", async () => {
    let getCalled = false;
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.includes("/settings/preferences")) {
        getCalled = true;
        return mockPreferences;
      }
      return {};
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <PreferencesTab />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      const textarea = screen.getByLabelText("Global Rules");
      expect(textarea).toHaveValue("# Rules\n- Use formal tone");
    });
    expect(getCalled).toBe(true);
    const upTextarea = screen.getByLabelText("User Preferences");
    expect(upTextarea).toHaveValue("# Preferences\n- Duration: 3min");
  });

  it("AC-3 saves preferences via PUT /api/settings/preferences", async () => {
    let putBody: unknown = null;
    vi.mocked(apiClient.get).mockImplementation(async (path: string) => {
      if (path.includes("/settings/preferences")) return mockPreferences;
      return {};
    });
    vi.mocked(apiClient.put).mockImplementation(async (_path: string, body: unknown) => {
      putBody = body;
      return { ok: true, snapshot_id: "snap_new" };
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <PreferencesTab />
      </QueryClientProvider>,
    );

    await waitFor(() =>
      expect(screen.getByLabelText("Global Rules")).toHaveValue("# Rules\n- Use formal tone"),
    );

    const textarea = screen.getByLabelText("Global Rules");
    await userEvent.clear(textarea);
    await userEvent.type(textarea, "# Updated Rules");

    await userEvent.click(screen.getByRole("button", { name: /保存配置/i }));

    await waitFor(() => {
      expect(putBody).toBeTruthy();
    });
    expect(putBody).toHaveProperty("global_rules_md");
  });
});
