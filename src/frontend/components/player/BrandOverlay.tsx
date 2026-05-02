// [SPEC-F-011] BrandOverlay — intro/outro/watermark/logo overlay for P11.
// Intro via Remotion Sequence prepend, outro append, watermark+logo via AbsoluteFill.
// Watermark opacity=0 hides watermark (AC-10). All frames have watermark when opacity>0 (AC-9).

import type { FC } from "react";
import { AbsoluteFill, Sequence, useCurrentFrame } from "remotion";
import type { BrandKit } from "../../render/brandKit";
import { resolveBrandKit } from "../../render/brandKit";

export interface BrandOverlayProps {
  /** brand_kit configuration (from API, not from file) */
  brandKit: BrandKit | null;
  /** Total duration of the video in frames */
  totalDurationInFrames: number;
  /** Frames per second */
  fps?: number;
  /** Whether to show the intro sequence */
  showIntro?: boolean;
  /** Whether to show the outro sequence */
  showOutro?: boolean;
}

/**
 * BrandOverlay manages P11 brand overlay elements:
 * - Intro sequence (prepended at frame 0)
 * - Outro sequence (appended at end)
 * - Watermark on all frames (when opacity > 0)
 * - Logo overlay
 */
const BrandOverlay: FC<BrandOverlayProps> = ({
  brandKit,
  totalDurationInFrames,
  fps = 30,
  showIntro = true,
  showOutro = true,
}) => {
  const frame = useCurrentFrame();
  const kit = resolveBrandKit(brandKit);

  const introDurationSec = kit.intro_template?.duration ?? 0;
  const introFrames = Math.round(introDurationSec * fps);
  const outroDurationSec = kit.outro_template?.duration ?? 0;
  const outroFrames = Math.round(outroDurationSec * fps);

  const watermark = kit.watermark;
  const renderWatermark = watermark && watermark.opacity > 0;

  return (
    <AbsoluteFill style={{ pointerEvents: "none" }}>
      {/* Intro sequence (prepended) */}
      {showIntro && introFrames > 0 && (
        <Sequence from={0} durationInFrames={introFrames} name="intro">
          <AbsoluteFill
            style={{
              backgroundColor: kit.color_palette.primary,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              opacity: 0.9,
            }}
          >
            {kit.logo_url && (
              <img
                src={kit.logo_url}
                alt="Brand logo"
                style={{ maxWidth: "40%", maxHeight: "40%" }}
              />
            )}
          </AbsoluteFill>
        </Sequence>
      )}

      {/* Outro sequence (appended) */}
      {showOutro && outroFrames > 0 && (
        <Sequence
          from={totalDurationInFrames - outroFrames}
          durationInFrames={outroFrames}
          name="outro"
        >
          <AbsoluteFill
            style={{
              backgroundColor: kit.color_palette.primary,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              opacity: 0.9,
            }}
          >
            <span
              style={{
                color: kit.color_palette.text,
                fontFamily: kit.font_family,
                fontSize: 24,
              }}
            >
              Thanks for watching
            </span>
          </AbsoluteFill>
        </Sequence>
      )}

      {/* Watermark on all frames (when opacity > 0) */}
      {renderWatermark && (
        <AbsoluteFill>
          <img
            src={watermark.url}
            alt="Watermark"
            style={{
              position: "absolute",
              opacity: watermark.opacity,
              ...getWatermarkPosition(watermark.position),
              maxWidth: "15%",
              maxHeight: "10%",
            }}
          />
        </AbsoluteFill>
      )}
    </AbsoluteFill>
  );
};

function getWatermarkPosition(
  position: "top_left" | "top_right" | "bottom_left" | "bottom_right",
): Record<string, string | number> {
  const positions: Record<string, Record<string, string | number>> = {
    top_left: { top: "2%", left: "2%" },
    top_right: { top: "2%", right: "2%" },
    bottom_left: { bottom: "4%", left: "2%" },
    bottom_right: { bottom: "4%", right: "2%" },
  };
  return positions[position] ?? positions.bottom_right;
}

export default BrandOverlay;
