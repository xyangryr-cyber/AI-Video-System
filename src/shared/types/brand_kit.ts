// BrandKit TypeScript interfaces (SPEC-0A.5).
// Mirror of src/shared/schemas/brand_kit.py.
// SQLite is the runtime authority; this file is import-only at the filesystem.

export type LogoPosition = "top_left" | "top_right" | "bottom_left" | "bottom_right";

export interface BrandKitLogo {
  path: string | null;
  position: LogoPosition;
  opacity: number;              // [0.0, 1.0]
}

export interface BrandKitWatermark {
  text: string | null;
  opacity: number;              // [0.0, 1.0]
  position: LogoPosition;
}

export interface BrandKitTemplate {
  template_id: string | null;
  duration: number;
}

export interface BrandKitColorPalette {
  primary: string;
  secondary: string;
  accent: string;
  background: string;
}

export interface BrandKit {
  logo: BrandKitLogo;
  watermark: BrandKitWatermark;
  intro_template: BrandKitTemplate;
  outro_template: BrandKitTemplate;
  color_palette: BrandKitColorPalette;
  font_family: string;
}
