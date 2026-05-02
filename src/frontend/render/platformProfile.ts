// [SPEC-F-011] Platform profiles — resolution and config per target platform.
// V1 supports 16:9 only. Other platforms return explicit deferral messages.
// All positioning uses percentages (no hardcoded pixel values).

export type TargetPlatform = "youtube_16_9" | "douyin" | "bilibili" | "twitter";

export interface PlatformProfile {
  platform: TargetPlatform;
  /** Display width in pixels */
  width: number;
  /** Display height in pixels */
  height: number;
  /** Whether this platform is supported in V1 */
  supported: boolean;
  /** Deferral message for unsupported platforms */
  deferral_message?: string;
  /** Safe zone margins as percentages of width/height */
  title_safe_percent: { top: number; bottom: number; left: number; right: number };
  /** Subtitle position as percentage from bottom */
  subtitle_bottom_percent: number;
}

export const PLATFORM_PROFILES: Record<TargetPlatform, PlatformProfile> = {
  youtube_16_9: {
    platform: "youtube_16_9",
    width: 1920,
    height: 1080,
    supported: true,
    title_safe_percent: { top: 5, bottom: 5, left: 5, right: 5 },
    subtitle_bottom_percent: 8,
  },
  douyin: {
    platform: "douyin",
    width: 1080,
    height: 1920,
    supported: false,
    deferral_message:
      "douyin (vertical 9:16) is not supported in V1 (16:9 only). Deferred to V1.5.",
    title_safe_percent: { top: 10, bottom: 15, left: 5, right: 5 },
    subtitle_bottom_percent: 12,
  },
  bilibili: {
    platform: "bilibili",
    width: 1920,
    height: 1080,
    supported: true,
    title_safe_percent: { top: 5, bottom: 5, left: 5, right: 5 },
    subtitle_bottom_percent: 8,
  },
  twitter: {
    platform: "twitter",
    width: 1280,
    height: 720,
    supported: true,
    title_safe_percent: { top: 5, bottom: 8, left: 3, right: 3 },
    subtitle_bottom_percent: 10,
  },
};

/**
 * Get the platform profile for a target platform.
 * Returns an explicit deferral message for unsupported platforms.
 */
export function getPlatformProfile(target: TargetPlatform): PlatformProfile {
  const profile = PLATFORM_PROFILES[target];
  if (!profile.supported) {
    console.warn(`Platform ${target}: ${profile.deferral_message}`);
  }
  return profile;
}

/**
 * Check if a platform is supported in V1.
 */
export function isPlatformSupported(target: TargetPlatform): boolean {
  return PLATFORM_PROFILES[target]?.supported ?? false;
}

/**
 * Get subtitle position as a percentage (no hardcoded pixels).
 */
export function getSubtitlePosition(platform: TargetPlatform): { bottom: string } {
  const profile = PLATFORM_PROFILES[platform];
  return {
    bottom: `${profile.subtitle_bottom_percent}%`,
  };
}
