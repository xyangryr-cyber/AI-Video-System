import type { ReactElement } from "react";
import type { ChartStyleConfig, StyleLock } from "@frontend/components/ChartConfirmDialog";

interface Props {
  styleConfig: ChartStyleConfig;
  styleLock: StyleLock;
  onChange: (styleConfig: ChartStyleConfig) => void;
  disabled?: boolean;
}

export function StyleEditor({ styleConfig, styleLock, onChange, disabled = false }: Props): ReactElement {
  const paletteColors = Object.values(styleLock.color_palette);

  const update = (field: string, value: string | boolean | number) => {
    onChange({ ...styleConfig, [field]: value });
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold">样式</h3>

      <div className="space-y-2">
        <label className="block text-xs">
          Line Color
          <div className="flex gap-1 mt-1 flex-wrap">
            {paletteColors.map((color) => (
              <button
                key={color}
                type="button"
                title={color}
                data-color={color}
                className={`w-6 h-6 rounded border-2 ${
                  styleConfig.line_color === color ? "border-blue-500" : "border-gray-300"
                }`}
                style={{ backgroundColor: color }}
                onClick={() => update("line_color", color)}
                disabled={disabled}
                aria-label={`Color ${color}`}
              />
            ))}
          </div>
        </label>

        <label className="flex items-center gap-2 text-xs">
          Line Width:
          <input
            type="range"
            min={1}
            max={5}
            value={styleConfig.line_width}
            onChange={(e) => update("line_width", Number(e.target.value))}
            disabled={disabled}
          />
          <span className="w-4 text-right">{styleConfig.line_width}</span>
        </label>

        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={styleConfig.smooth}
            onChange={(e) => update("smooth", e.target.checked)}
            disabled={disabled}
          />
          Smooth
        </label>

        <label className="block text-xs">
          Background Color
          <div className="flex gap-1 mt-1 flex-wrap">
            {paletteColors.map((color) => (
              <button
                key={color}
                type="button"
                title={color}
                data-color={color}
                className={`w-6 h-6 rounded border-2 ${
                  styleConfig.background_color === color ? "border-blue-500" : "border-gray-300"
                }`}
                style={{ backgroundColor: color }}
                onClick={() => update("background_color", color)}
                disabled={disabled}
                aria-label={`Background ${color}`}
              />
            ))}
          </div>
        </label>

        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={styleConfig.grid_visible}
            onChange={(e) => update("grid_visible", e.target.checked)}
            disabled={disabled}
          />
          Grid Visible
        </label>

        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={styleConfig.show_source_label}
            onChange={(e) => update("show_source_label", e.target.checked)}
            disabled={disabled}
          />
          Show Source Label
        </label>

        <label className="flex items-center gap-2 text-xs">
          Animation (ms):
          <input
            type="number"
            min={0}
            max={3000}
            className="border rounded px-1 py-0.5 w-20"
            value={styleConfig.animation_duration_ms}
            onChange={(e) => update("animation_duration_ms", Number(e.target.value))}
            disabled={disabled}
          />
        </label>
      </div>
    </div>
  );
}
