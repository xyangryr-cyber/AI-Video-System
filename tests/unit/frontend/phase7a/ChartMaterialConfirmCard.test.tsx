import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { ChartMaterialConfirmCard } from "@frontend/components/phase7a/ChartMaterialConfirmCard";
import type { ChartMaterialView, AxisSpec } from "@frontend/types/chart_material";
import type { ChartChangeRequest } from "@frontend/components/phase7a/ChartMaterialConfirmCard";

const axisSpec: AxisSpec = {
  x_axis: {
    type: "time",
    labels: ["2024-01", "2024-06"],
    range: ["2024-01-01", "2024-06-30"],
  },
  y_axis: {
    unit: "万元",
    min: 0,
    max: 100,
    scale_mode: "linear",
  },
};

const chartMaterial: ChartMaterialView = {
  chart_id: "chart_1",
  shot_id: "shot_1",
  metric_name: "营收趋势",
  date_range: { start: "2024-01-01", end: "2024-06-30" },
  granularity: "month",
  source: { provider: "东方财富", symbol: "000001.SZ" },
  verification_status: "verified",
  chart_spec: { kind: "line", series: [] },
  axis_spec: axisSpec,
};

describe("ChartMaterialConfirmCard", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe("AC-3: renders axis_spec and change request", () => {
    it("renders x_axis time range", () => {
      render(
        <ChartMaterialConfirmCard
          chartMaterial={chartMaterial}
          onRequestChange={vi.fn()}
        />,
      );
      expect(screen.getByText(/2024-01-01/)).toBeInTheDocument();
      expect(screen.getByText(/2024-06-30/)).toBeInTheDocument();
    });

    it("renders y_axis unit min max", () => {
      render(
        <ChartMaterialConfirmCard
          chartMaterial={chartMaterial}
          onRequestChange={vi.fn()}
        />,
      );
      expect(screen.getByText(/万元/)).toBeInTheDocument();
      expect(screen.getByText(/\[0, 100\]/)).toBeInTheDocument();
    });

    it("calls onRequestChange with ChartChangeRequest when 请求修改 is clicked", () => {
      const onChange = vi.fn();
      render(
        <ChartMaterialConfirmCard
          chartMaterial={chartMaterial}
          onRequestChange={onChange}
        />,
      );
      const btn = screen.getByRole("button", { name: /请求修改|request change/i });
      fireEvent.click(btn);
      expect(onChange).toHaveBeenCalledTimes(1);
      const arg = onChange.mock.calls[0][0] as ChartChangeRequest;
      expect(arg.chart_id).toBe("chart_1");
      expect(arg.shot_id).toBe("shot_1");
    });
  });
});
