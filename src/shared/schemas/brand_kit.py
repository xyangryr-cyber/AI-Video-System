"""BrandKit Pydantic model (SPEC-0A.5).

SQLite is the runtime authority for brand_kit; the filesystem file
data/users/{user_id}/brand_kit.json is import-only.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

LogoPosition = Literal["top_left", "top_right", "bottom_left", "bottom_right"]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class BrandKitLogo(_Strict):
    path: str | None = None
    position: LogoPosition
    opacity: float = Field(ge=0.0, le=1.0)


class BrandKitWatermark(_Strict):
    text: str | None = None
    opacity: float = Field(ge=0.0, le=1.0)
    position: LogoPosition


class BrandKitTemplate(_Strict):
    template_id: str | None = None
    duration: float = Field(ge=0.0)


class BrandKitColorPalette(_Strict):
    primary: str = Field(min_length=1)
    secondary: str = Field(min_length=1)
    accent: str = Field(min_length=1)
    background: str = Field(min_length=1)


class BrandKit(_Strict):
    logo: BrandKitLogo
    watermark: BrandKitWatermark
    intro_template: BrandKitTemplate
    outro_template: BrandKitTemplate
    color_palette: BrandKitColorPalette
    font_family: str = Field(min_length=1)


__all__ = [
    "BrandKit",
    "BrandKitColorPalette",
    "BrandKitLogo",
    "BrandKitTemplate",
    "BrandKitWatermark",
    "LogoPosition",
]
