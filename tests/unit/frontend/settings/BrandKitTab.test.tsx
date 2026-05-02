import { describe, it, expect, beforeEach, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { QueryClientProvider } from "@tanstack/react-query";
import { createQueryClient } from "@frontend/lib/queryClient";
import { BrandKitTab } from "@frontend/components/settings/BrandKitTab";
import { apiClient } from "@frontend/api/client";

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: vi.fn(), post: vi.fn(), put: vi.fn(), delete: vi.fn() },
}));

beforeEach(() => {
  vi.clearAllMocks();
});

describe("BrandKitTab", () => {
  it("AC-4 saves brand kit via PUT /api/settings/brand-kit", async () => {
    let putBody: unknown = null;
    vi.mocked(apiClient.put).mockImplementation(async (_path: string, body: unknown) => {
      putBody = body;
      return { ok: true };
    });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <BrandKitTab />
      </QueryClientProvider>,
    );

    await waitFor(() => expect(screen.getByLabelText(/字体/i)).toBeInTheDocument());

    const fontInput = screen.getByLabelText(/字体/i);
    await userEvent.clear(fontInput);
    await userEvent.type(fontInput, "Inter");

    await userEvent.click(screen.getByRole("button", { name: /保存品牌配置/i }));

    await waitFor(() => {
      expect(putBody).toBeTruthy();
    });
    expect(putBody).toHaveProperty("font_family", "Inter");
  });

  it("AC-4 renders all brand kit fields", () => {
    vi.mocked(apiClient.put).mockResolvedValue({ ok: true });

    render(
      <QueryClientProvider client={createQueryClient()}>
        <BrandKitTab />
      </QueryClientProvider>,
    );

    expect(screen.getByLabelText(/字体/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/主色/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/辅色/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/强调色/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/背景色/i)).toBeInTheDocument();
  });
});
