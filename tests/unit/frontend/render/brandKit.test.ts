import { describe, it, expect, vi } from "vitest";

const mockGet = vi.hoisted(() => vi.fn());

vi.mock("@frontend/api/client", () => ({
  apiClient: { get: mockGet },
}));

import { fetchBrandKit, SYSTEM_DEFAULTS, resolveBrandKit, getPrimaryColor } from "@frontend/render/brandKit";

describe("fetchBrandKit", () => {
  it("calls apiClient.get with /api/settings", async () => {
    mockGet.mockResolvedValueOnce({ brand_kit: { color_palette: { primary: "#111" } } });

    await fetchBrandKit();

    expect(mockGet).toHaveBeenCalledWith("/api/settings");
  });

  it("returns BrandKit when API responds with brand_kit", async () => {
    const kit = { color_palette: { primary: "#test123" }, font_family: "Arial" };
    mockGet.mockResolvedValueOnce({ brand_kit: kit });

    const result = await fetchBrandKit();

    expect(result).toEqual(kit);
  });

  it("returns null when API responds without brand_kit", async () => {
    mockGet.mockResolvedValueOnce({ model_config_data: {} });

    const result = await fetchBrandKit();

    expect(result).toBeNull();
  });

  it("returns null when apiClient throws", async () => {
    mockGet.mockRejectedValueOnce(new Error("Network error"));

    const result = await fetchBrandKit();

    expect(result).toBeNull();
  });
});

describe("resolveBrandKit", () => {
  it("returns SYSTEM_DEFAULTS when brandKit is null", () => {
    expect(resolveBrandKit(null)).toBe(SYSTEM_DEFAULTS);
  });

  it("returns brandKit when provided", () => {
    const kit = { ...SYSTEM_DEFAULTS, color_palette: { ...SYSTEM_DEFAULTS.color_palette, primary: "#custom" }, font_family: "Custom" };
    expect(resolveBrandKit(kit)).toBe(kit);
  });
});

describe("getPrimaryColor", () => {
  it("returns override when provided", () => {
    expect(getPrimaryColor(null, "#override")).toBe("#override");
  });

  it("returns brandKit primary when no override", () => {
    const kit = { ...SYSTEM_DEFAULTS, color_palette: { ...SYSTEM_DEFAULTS.color_palette, primary: "#fromKit" }, font_family: "F" };
    expect(getPrimaryColor(kit)).toBe("#fromKit");
  });

  it("returns system default when no brandKit and no override", () => {
    expect(getPrimaryColor(null)).toBe(SYSTEM_DEFAULTS.color_palette.primary);
  });
});
