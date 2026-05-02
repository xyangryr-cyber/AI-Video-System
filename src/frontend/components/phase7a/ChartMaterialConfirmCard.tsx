import type { ReactElement } from "react";
import type { ChartMaterialView } from "@frontend/types/chart_material";

export interface ChartChangeRequest {
  chart_id: string;
  shot_id: string;
  reason: string;
}

interface Props {
  chartMaterial: ChartMaterialView;
  onRequestChange: (req: ChartChangeRequest) => void;
}

export function ChartMaterialConfirmCard({ chartMaterial, onRequestChange }: Props): ReactElement {
  const xAxis = chartMaterial.axis_spec.x_axis;
  const yAxis = chartMaterial.axis_spec.y_axis;

  return (
    <div data-testid="chart-confirm-card" className="border rounded p-4">
      <h3 className="text-sm font-medium mb-2">
        {chartMaterial.chart_id}: {chartMaterial.metric_name}
      </h3>

      <div className="space-y-2 text-xs">
        <div>
          <span className="text-gray-500">X 轴范围: </span>
          <span>
            {String(xAxis.range[0])} ~ {String(xAxis.range[1])}
          </span>
        </div>
        <div>
          <span className="text-gray-500">Y 轴: </span>
          <span>
            {yAxis.unit} [{yAxis.min}, {yAxis.max}]
          </span>
        </div>
      </div>

      <button
        aria-label="请求修改"
        className="mt-3 px-3 py-1 text-xs border rounded"
        onClick={() =>
          onRequestChange({
            chart_id: chartMaterial.chart_id,
            shot_id: chartMaterial.shot_id,
            reason: "用户请求修改 axis_spec",
          })
        }
      >
        请求修改
      </button>
    </div>
  );
}
