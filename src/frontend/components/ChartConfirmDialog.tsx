import { useState, type ReactElement } from "react";
import type { StyleLock as SharedStyleLock } from "@shared/types/artifacts";
import { ClarificationQuestionList } from "@frontend/components/chart/ClarificationQuestionList";
import { DataSourceBadge } from "@frontend/components/chart/DataSourceBadge";
import { AxisEditor } from "@frontend/components/chart/AxisEditor";
import { StyleEditor } from "@frontend/components/chart/StyleEditor";

// Re-export types for consumers
export type StyleLock = SharedStyleLock;

export type ChartIntentStatus =
  | "awaiting_clarification"
  | "awaiting_confirmation"
  | "rendering"
  | "done"
  | "cancelled";

export interface ChartDataPreview {
  chart_type: "line" | "bar" | "pie";
  time_range: string;
  frequency: string;
  unit: string;
  source_label: string;
  thumbnail_url?: string;
}

export interface AxisSettings {
  label: string;
  unit: string;
  min?: number;
  max?: number;
  zero_based: boolean;
}

export interface AxisConfig {
  x_axis: AxisSettings;
  y_axis: AxisSettings;
}

export interface ChartStyleConfig {
  line_width: number;
  line_color: string;
  smooth: boolean;
  background_color: string;
  grid_visible: boolean;
  show_source_label: boolean;
  animation_duration_ms: number;
}

export interface ChartIntent {
  id: string;
  status: ChartIntentStatus;
  clarification_questions?: string[];
  data_preview?: ChartDataPreview;
  data_source_verified: boolean;
  axis_config: AxisConfig;
  style_config: ChartStyleConfig;
}

export interface ChartStyleOverrides {
  axis_config?: Partial<AxisConfig>;
  style_config?: Partial<ChartStyleConfig>;
}

interface Props {
  open: boolean;
  chart_intent: ChartIntent;
  style_lock: StyleLock;
  onClose: () => void;
  onConfirm: (overrides: ChartStyleOverrides) => void;
  onBackToClarify: () => void;
}

export function ChartConfirmDialog({
  open,
  chart_intent,
  style_lock,
  onClose,
  onConfirm,
  onBackToClarify,
}: Props): ReactElement | null {
  const [answers, setAnswers] = useState<Record<number, string>>({});
  const [axisConfig, setAxisConfig] = useState<AxisConfig>(chart_intent.axis_config);
  const [styleConfig, setStyleConfig] = useState<ChartStyleConfig>(chart_intent.style_config);

  if (!open) return null;

  const isDisabled =
    chart_intent.status === "rendering" ||
    chart_intent.status === "done" ||
    chart_intent.status === "cancelled";

  const handleAnswerChange = (index: number, value: string) => {
    setAnswers((prev) => ({ ...prev, [index]: value }));
  };

  const handleSubmitClarification = () => {
    // In a real implementation this would POST answers to the backend.
    // For now, the callback signals completion.
  };

  const handleConfirm = () => {
    onConfirm({
      axis_config: axisConfig,
      style_config: styleConfig,
    });
  };

  if (chart_intent.status === "awaiting_clarification") {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md space-y-4">
          <h2 className="text-lg font-bold">图表确认</h2>
          <ClarificationQuestionList
            questions={chart_intent.clarification_questions || []}
            answers={answers}
            onAnswerChange={handleAnswerChange}
            onSubmit={handleSubmitClarification}
            disabled={isDisabled}
          />
          <div className="flex justify-end gap-2">
            <button
              type="button"
              className="px-3 py-1 text-sm border rounded"
              onClick={onClose}
              disabled={isDisabled}
            >
              取消
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (chart_intent.status === "rendering") {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md space-y-4 text-center">
          <h2 className="text-lg font-bold">渲染中</h2>
          <p className="text-sm text-gray-500">图表正在渲染，请稍候...</p>
          <div className="animate-pulse h-1 bg-blue-500 rounded" />
        </div>
      </div>
    );
  }

  if (chart_intent.status === "done") {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md space-y-4 text-center">
          <h2 className="text-lg font-bold text-green-600">完成</h2>
          <p className="text-sm text-gray-500">图表已成功渲染。</p>
          <button type="button" className="px-4 py-1 bg-gray-200 rounded text-sm" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    );
  }

  if (chart_intent.status === "cancelled") {
    return (
      <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md space-y-4 text-center">
          <h2 className="text-lg font-bold text-gray-500">已取消</h2>
          <p className="text-sm text-gray-500">图表请求已取消。</p>
          <button type="button" className="px-4 py-1 bg-gray-200 rounded text-sm" onClick={onClose}>
            关闭
          </button>
        </div>
      </div>
    );
  }

  // awaiting_confirmation
  const dataPreview = chart_intent.data_preview;
  return (
    <div className="fixed inset-0 bg-black/30 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-lg space-y-4 max-h-[90vh] overflow-y-auto">
        <h2 className="text-lg font-bold">图表确认</h2>

        {dataPreview && (
          <div className="border rounded p-3 space-y-2 bg-gray-50">
            <h3 className="text-sm font-semibold">数据预览</h3>
            <p className="text-xs">
              <span className="text-gray-500">时间范围:</span> {dataPreview.time_range}
            </p>
            <p className="text-xs">
              <span className="text-gray-500">频率:</span> {dataPreview.frequency}
            </p>
            <p className="text-xs">
              <span className="text-gray-500">单位:</span> {dataPreview.unit}
            </p>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">来源:</span>
              <DataSourceBadge
                verified={chart_intent.data_source_verified}
                sourceLabel={dataPreview.source_label}
              />
            </div>
          </div>
        )}

        <AxisEditor axisConfig={axisConfig} onChange={setAxisConfig} disabled={isDisabled} />

        <StyleEditor
          styleConfig={styleConfig}
          styleLock={style_lock}
          onChange={setStyleConfig}
          disabled={isDisabled}
        />

        <div className="flex justify-between pt-2 border-t">
          <div className="flex gap-2">
            <button
              type="button"
              className="px-3 py-1 text-sm border rounded"
              onClick={onBackToClarify}
              disabled={isDisabled}
            >
              上一步澄清
            </button>
            <button
              type="button"
              className="px-3 py-1 text-sm border rounded text-gray-500"
              onClick={onClose}
              disabled={isDisabled}
            >
              取消
            </button>
          </div>
          <button
            type="button"
            className="px-4 py-1 text-sm bg-blue-500 text-white rounded disabled:opacity-50"
            disabled={isDisabled || !chart_intent.data_source_verified}
            onClick={handleConfirm}
          >
            确认渲染
          </button>
        </div>
      </div>
    </div>
  );
}
