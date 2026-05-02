import type { ReactElement } from "react";
import type { AxisConfig } from "@frontend/components/ChartConfirmDialog";

interface Props {
  axisConfig: AxisConfig;
  onChange: (axisConfig: AxisConfig) => void;
  disabled?: boolean;
}

export function AxisEditor({ axisConfig, onChange, disabled = false }: Props): ReactElement {
  const updateX = (field: string, value: string | boolean | number) => {
    onChange({
      ...axisConfig,
      x_axis: { ...axisConfig.x_axis, [field]: value },
    });
  };

  const updateY = (field: string, value: string | boolean | number | undefined) => {
    onChange({
      ...axisConfig,
      y_axis: { ...axisConfig.y_axis, [field]: value },
    });
  };

  return (
    <div className="space-y-3">
      <h3 className="text-sm font-semibold">坐标轴</h3>

      <fieldset className="border rounded p-2 space-y-2">
        <legend className="text-xs font-medium">X 轴</legend>
        <label className="flex items-center gap-2 text-xs">
          Label:
          <input
            type="text"
            className="border rounded px-1 py-0.5 flex-1"
            value={axisConfig.x_axis.label}
            onChange={(e) => updateX("label", e.target.value)}
            disabled={disabled}
          />
        </label>
        <label className="flex items-center gap-2 text-xs">
          Unit:
          <input
            type="text"
            className="border rounded px-1 py-0.5 flex-1"
            value={axisConfig.x_axis.unit}
            onChange={(e) => updateX("unit", e.target.value)}
            disabled={disabled}
          />
        </label>
        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={axisConfig.x_axis.zero_based}
            onChange={(e) => updateX("zero_based", e.target.checked)}
            disabled={disabled}
          />
          Zero-based
        </label>
      </fieldset>

      <fieldset className="border rounded p-2 space-y-2">
        <legend className="text-xs font-medium">Y 轴</legend>
        <label className="flex items-center gap-2 text-xs">
          Label:
          <input
            type="text"
            className="border rounded px-1 py-0.5 flex-1"
            value={axisConfig.y_axis.label}
            onChange={(e) => updateY("label", e.target.value)}
            disabled={disabled}
          />
        </label>
        <label className="flex items-center gap-2 text-xs">
          Unit:
          <input
            type="text"
            className="border rounded px-1 py-0.5 flex-1"
            value={axisConfig.y_axis.unit}
            onChange={(e) => updateY("unit", e.target.value)}
            disabled={disabled}
          />
        </label>
        <label className="flex items-center gap-2 text-xs">
          Min:
          <input
            type="number"
            className="border rounded px-1 py-0.5 w-24"
            value={axisConfig.y_axis.min ?? ""}
            onChange={(e) =>
              updateY("min", e.target.value === "" ? undefined : Number(e.target.value))
            }
            disabled={disabled}
          />
        </label>
        <label className="flex items-center gap-2 text-xs">
          Max:
          <input
            type="number"
            className="border rounded px-1 py-0.5 w-24"
            value={axisConfig.y_axis.max ?? ""}
            onChange={(e) =>
              updateY("max", e.target.value === "" ? undefined : Number(e.target.value))
            }
            disabled={disabled}
          />
        </label>
        <label className="flex items-center gap-2 text-xs">
          <input
            type="checkbox"
            checked={axisConfig.y_axis.zero_based}
            onChange={(e) => updateY("zero_based", e.target.checked)}
            disabled={disabled}
          />
          Zero-based
        </label>
      </fieldset>
    </div>
  );
}
