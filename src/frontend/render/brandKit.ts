// [SPEC-F-011] Brand kit — inheritance, override, and API-based fetching.
// brand_kit is fetched from API (GET /api/settings), not from disk.
// New projects inherit brand_kit; project-level overrides take precedence.

import { apiClient } from "@frontend/api/client";

export interface BrandKit {
  logo_url?: string;
  watermark?: {
    url: string;
    opacity: number;
    position: "top_left" | "top_right" | "bottom_left" | "bottom_right";
  };
  intro_template?: {
    template_id: string;
    duration: number; // seconds
  };
  outro_template?: {
    template_id: string;
    duration: number;
  };
  color_palette: {
    primary: string;
    secondary: string;
    accent: string;
    background: string;
    text: string;
  };
  font_family: string;
}

/** System defaults when no brand_kit is configured. */
export const SYSTEM_DEFAULTS: BrandKit = {
  color_palette: {
    primary: "#1a73e8",
    secondary: "#34a853",
    accent: "#ea4335",
    background: "#ffffff",
    text: "#202124",
  },
  font_family: "Noto Sans SC, sans-serif",
};

/**
 * Fetch brand_kit from the API (GET /api/settings).
 * Never reads the config file directly from disk.
 */
export async function fetchBrandKit(): Promise<BrandKit | null> {
  try {
    const data = await apiClient.get<{ brand_kit: BrandKit | null }>("/api/settings");
    return data.brand_kit ?? null;
  } catch {
    return null;
  }
}

/**
 * Merge project-level overrides into the brand_kit.
 * Un-overridden fields inherit from brand_kit.
 */
export function mergeBrandKit(
  brandKit: BrandKit | null,
  projectOverrides: Partial<BrandKit>
): BrandKit {
  const base = brandKit ?? SYSTEM_DEFAULTS;

  return {
    ...base,
    ...projectOverrides,
    color_palette: {
      ...base.color_palette,
      ...(projectOverrides.color_palette ?? {}),
    },
  };
}

/**
 * Resolve the effective brand_kit for rendering.
 * Falls back to SYSTEM_DEFAULTS when brand_kit is null/missing.
 */
export function resolveBrandKit(brandKit: BrandKit | null): BrandKit {
  return brandKit ?? SYSTEM_DEFAULTS;
}

/**
 * Get the primary color for rendering.
 * Project override wins over brand_kit default over system default.
 */
export function getPrimaryColor(
  brandKit: BrandKit | null,
  overrideColor?: string
): string {
  if (overrideColor) return overrideColor;
  if (brandKit?.color_palette.primary) return brandKit.color_palette.primary;
  return SYSTEM_DEFAULTS.color_palette.primary;
}
