import type { ReactElement } from "react";
import { useState } from "react";
import { useBrandKitMutation } from "../../hooks/useSettings";
import type { BrandKit } from "@shared/types/brand_kit";

const DEFAULT_BRAND_KIT: BrandKit = {
  logo: { path: null, position: "top_left", opacity: 0.8 },
  watermark: { text: null, opacity: 0.3, position: "bottom_right" },
  intro_template: { template_id: null, duration: 3.0 },
  outro_template: { template_id: null, duration: 3.0 },
  color_palette: { primary: "#1a73e8", secondary: "#34a853", accent: "#ea4335", background: "#ffffff" },
  font_family: "Noto Sans SC",
};

export function BrandKitTab(): ReactElement {
  const saveMutation = useBrandKitMutation();
  const [fontFamily, setFontFamily] = useState(DEFAULT_BRAND_KIT.font_family);
  const [primary, setPrimary] = useState(DEFAULT_BRAND_KIT.color_palette.primary);
  const [secondary, setSecondary] = useState(DEFAULT_BRAND_KIT.color_palette.secondary);
  const [accent, setAccent] = useState(DEFAULT_BRAND_KIT.color_palette.accent);
  const [background, setBackground] = useState(DEFAULT_BRAND_KIT.color_palette.background);

  function buildPayload(): BrandKit {
    return {
      ...DEFAULT_BRAND_KIT,
      font_family: fontFamily,
      color_palette: { primary, secondary, accent, background },
    };
  }

  return (
    <div data-testid="brand-kit-tab" className="bg-white rounded-2xl border-2 border-slate-200 overflow-hidden flex flex-col">
      <div className="p-6 border-b border-slate-200 shrink-0">
        <h2 className="text-[0.85rem] font-bold text-[#1e293b] uppercase tracking-[0.05em]">品牌包配置 (Brand Kit)</h2>
        <p className="text-sm text-slate-500 mt-1">字体与色彩方案，用于视频输出统一品牌视觉。</p>
      </div>
      <div className="p-6 space-y-6">
        <div>
          <label htmlFor="font-family" className="block text-sm font-medium text-slate-700 mb-2">字体 (Font Family)</label>
          <input
            id="font-family" value={fontFamily}
            onChange={(e) => setFontFamily(e.target.value)}
            className="w-full bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
          />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label htmlFor="color-primary" className="block text-sm font-medium text-slate-700 mb-2">主色 (Primary)</label>
            <div className="flex gap-2">
              <input
                id="color-primary" value={primary}
                onChange={(e) => setPrimary(e.target.value)}
                className="flex-1 bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 font-mono"
              />
              <span className="w-10 h-10 rounded-lg border border-slate-200 shrink-0" style={{ backgroundColor: primary }}></span>
            </div>
          </div>
          <div>
            <label htmlFor="color-secondary" className="block text-sm font-medium text-slate-700 mb-2">辅色 (Secondary)</label>
            <div className="flex gap-2">
              <input
                id="color-secondary" value={secondary}
                onChange={(e) => setSecondary(e.target.value)}
                className="flex-1 bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 font-mono"
              />
              <span className="w-10 h-10 rounded-lg border border-slate-200 shrink-0" style={{ backgroundColor: secondary }}></span>
            </div>
          </div>
          <div>
            <label htmlFor="color-accent" className="block text-sm font-medium text-slate-700 mb-2">强调色 (Accent)</label>
            <div className="flex gap-2">
              <input
                id="color-accent" value={accent}
                onChange={(e) => setAccent(e.target.value)}
                className="flex-1 bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 font-mono"
              />
              <span className="w-10 h-10 rounded-lg border border-slate-200 shrink-0" style={{ backgroundColor: accent }}></span>
            </div>
          </div>
          <div>
            <label htmlFor="color-background" className="block text-sm font-medium text-slate-700 mb-2">背景色 (Background)</label>
            <div className="flex gap-2">
              <input
                id="color-background" value={background}
                onChange={(e) => setBackground(e.target.value)}
                className="flex-1 bg-slate-50 border border-slate-300 text-slate-900 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5 font-mono"
              />
              <span className="w-10 h-10 rounded-lg border border-slate-200 shrink-0" style={{ backgroundColor: background }}></span>
            </div>
          </div>
        </div>
        <div className="pt-6 border-t border-slate-100 flex justify-end">
          <button
            onClick={() => saveMutation.mutate(buildPayload())}
            className="flex items-center px-6 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg font-medium shadow-sm transition-colors"
          >
            <svg className="w-4 h-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}><path strokeLinecap="round" strokeLinejoin="round" d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" /></svg>
            保存品牌配置
          </button>
        </div>
      </div>
    </div>
  );
}
