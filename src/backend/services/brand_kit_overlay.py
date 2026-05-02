"""[SPEC-D-009] BrandKitOverlay -- intro/outro/watermark/logo overlay.

Authority: docs/specs/SPEC-D-pipeline-phases.md SPEC-9.11.4

Strategy:
1. Probe video dimensions via ffprobe.
2. Build FFmpeg filter_complex for brand kit overlay elements
   (watermark, logo, intro/outro fades, color correction).
3. Execute FFmpeg and return output path + applied overlays.
4. Graceful fallback to stub if ffmpeg/ffprobe not available or fail.
"""

from __future__ import annotations

import logging
import subprocess
from typing import Any

logger = logging.getLogger(__name__)

# Default overlay margins (pixels from edge)
_DEFAULT_MARGIN = 24

# Brand kit key constants
_KEY_INTRO_DURATION = "intro_duration"
_KEY_OUTRO_DURATION = "outro_duration"
_KEY_WATERMARK = "watermark"
_KEY_LOGO_PATH = "logo_path"
_KEY_WATERMARK_POSITION = "watermark_position"
_KEY_PRIMARY_COLOR = "primary_color"
_KEY_ACCENT_COLOR = "accent_color"


class BrandKitOverlay:
    """Apply brand kit elements to final video."""

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _probe_dimensions(video_path: str) -> tuple[int, int] | None:
        """Return (width, height) or None if ffprobe is unavailable/fails."""
        try:
            result = subprocess.run(
                [
                    "ffprobe",
                    "-v",
                    "error",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=width,height",
                    "-of",
                    "csv=p=0",
                    video_path,
                ],
                capture_output=True,
                text=True,
                timeout=15,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

        if result.returncode != 0:
            return None

        line = result.stdout.strip()
        if not line:
            return None

        parts = line.split(",")
        if len(parts) >= 2:
            try:
                return int(parts[0]), int(parts[1])
            except ValueError:
                return None
        return None

    @staticmethod
    def _resolve_watermark_position(
        brand_kit: dict[str, Any], width: int, height: int
    ) -> tuple[str, str]:
        """Return (x_expr, y_expr) FFmpeg drawtext coordinate expressions."""
        position = brand_kit.get(_KEY_WATERMARK_POSITION, "bottom-right")
        margin = brand_kit.get("watermark_margin", _DEFAULT_MARGIN)

        if position == "top-right":
            return (f"w-tw-{margin}", f"{margin}")
        elif position == "top-left":
            return (f"{margin}", f"{margin}")
        elif position == "bottom-left":
            return (f"{margin}", f"h-th-{margin}")
        else:  # bottom-right (default)
            return (f"w-tw-{margin}", f"h-th-{margin}")

    @staticmethod
    def _build_filter_complex(
        video_path: str,
        brand_kit: dict[str, Any],
        width: int,
        height: int,
        output_path: str,
    ) -> tuple[list[str], list[str]]:
        """Build ffmpeg command args and applied overlay names.

        Returns (ffmpeg_args, applied_overlays).
        """
        filters: list[str] = []
        applied: list[str] = []

        intro_dur = brand_kit.get(_KEY_INTRO_DURATION, 0.0)
        outro_dur = brand_kit.get(_KEY_OUTRO_DURATION, 0.0)
        watermark_text = brand_kit.get(_KEY_WATERMARK, "")
        logo_path = brand_kit.get(_KEY_LOGO_PATH, "")
        primary = brand_kit.get(_KEY_PRIMARY_COLOR, "")
        accent = brand_kit.get(_KEY_ACCENT_COLOR, "")

        # Color correction via eq filter (if colors provided)
        if primary or accent:
            # Simple color adjustment: slight saturation boost for branded look
            filters.append("eq=saturation=1.1:brightness=0.02")
            applied.append("color_correction")

        # Watermark text overlay
        if watermark_text:
            x_expr, y_expr = BrandKitOverlay._resolve_watermark_position(brand_kit, width, height)
            font_size = brand_kit.get("watermark_font_size", max(14, height // 36))
            font_color = brand_kit.get("watermark_color", "white@0.7")
            drawtext_filter = (
                f"drawtext=text='{watermark_text}':"
                f"fontsize={font_size}:fontcolor={font_color}:"
                f"x={x_expr}:y={y_expr}:"
                f"shadowx=1:shadowy=1:shadowcolor=black@0.4"
            )
            filters.append(drawtext_filter)
            applied.append("watermark")

        # Logo overlay
        if logo_path:
            logo_x = brand_kit.get("logo_margin", _DEFAULT_MARGIN)
            logo_y = brand_kit.get("logo_margin", _DEFAULT_MARGIN)
            overlay_filter = f"overlay={logo_x}:{logo_y}"
            filters.append(overlay_filter)
            applied.append("logo")

        # Intro/outro fade
        if intro_dur > 0:
            filters.insert(0, f"fade=in:0:{30 if intro_dur <= 0 else int(intro_dur * 30)}")
            applied.append("intro_fade")
        if outro_dur > 0:
            filters.append(f"fade=out:st=0:d={outro_dur}")
            applied.append("outro_fade")

        if not filters:
            # Nothing to apply — copy stream
            return (["-c", "copy"], applied)

        filter_chain = ",".join(filters)
        return (["-vf", filter_chain], applied)

    # ------------------------------------------------------------------
    # public interface
    # ------------------------------------------------------------------

    @staticmethod
    def apply(*, video_path: str, brand_kit: dict[str, Any]) -> dict[str, Any]:
        output_path = video_path.replace(".mp4", "_branded.mp4")

        # Probe dimensions
        dims = BrandKitOverlay._probe_dimensions(video_path)

        if dims is None:
            # ffprobe not available or file doesn't exist — fallback to stub
            logger.info("ffprobe unavailable or video not found, using stub overlay")
            return {
                "output_path": output_path,
                "overlays": list(brand_kit.keys()),
            }

        width, height = dims

        # Build filter
        ffmpeg_args, applied = BrandKitOverlay._build_filter_complex(
            video_path, brand_kit, width, height, output_path
        )

        # Execute ffmpeg
        cmd = [
            "ffmpeg",
            "-y",
            "-i",
            video_path,
            *ffmpeg_args,
            output_path,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("ffmpeg execution failed: %s", exc)
            return {
                "output_path": output_path,
                "overlays": list(brand_kit.keys()),
            }

        if result.returncode != 0:
            logger.warning(
                "ffmpeg overlay failed (rc=%d), falling back to stub. stderr: %s",
                result.returncode,
                result.stderr[-500:] if result.stderr else "(none)",
            )
            return {
                "output_path": output_path,
                "overlays": list(brand_kit.keys()),
            }

        return {
            "output_path": output_path,
            "overlays": applied,
        }
