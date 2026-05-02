import type { ReactElement } from "react";

interface Props {
  materialId: string;
  status: string;
  rationale: string;
  source: string;
  evidence: string;
  onRequestRefetch: (materialId: string) => void;
  onClose: () => void;
}

const STATUS_LABELS: Record<string, string> = {
  missing: "缺失",
  rejected: "未通过",
  pending: "待验证",
  verified: "已验证",
};

export function MaterialDetailDrawer({
  materialId,
  status,
  rationale,
  source,
  evidence,
  onRequestRefetch,
  onClose,
}: Props): ReactElement {
  return (
    <div
      data-testid="material-detail-drawer"
      className="fixed inset-y-0 right-0 w-80 bg-white shadow-lg border-l p-4 overflow-y-auto"
      role="dialog"
      aria-label="素材详情"
    >
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-sm font-medium">{materialId}</h3>
        <button aria-label="关闭" className="text-gray-400 text-lg" onClick={onClose}>
          ×
        </button>
      </div>

      <div className="space-y-3 text-xs">
        <div>
          <span className="text-gray-500">状态: </span>
          <span className="font-medium">{STATUS_LABELS[status] || status}</span>
        </div>
        <div>
          <span className="text-gray-500">理由: </span>
          <span>{rationale}</span>
        </div>
        <div>
          <span className="text-gray-500">来源: </span>
          <span>{source}</span>
        </div>
        <div>
          <span className="text-gray-500">证据: </span>
          <span>{evidence}</span>
        </div>
      </div>

      <div className="mt-4 space-y-2">
        <button
          aria-label="重抓"
          className="w-full px-3 py-1 text-xs border rounded bg-blue-50"
          onClick={() => onRequestRefetch(materialId)}
        >
          重抓
        </button>
      </div>
    </div>
  );
}
