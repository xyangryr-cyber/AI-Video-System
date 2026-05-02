import type { ReactElement } from "react";

interface SegmentEntry {
  id: string;
  index: number;
  preview_url: string;
  text: string;
}

interface Props {
  segments: SegmentEntry[];
  confirmed: boolean;
  onMixFeedback: (segmentId: string) => void;
}

export function Phase6SegmentMixList({ segments, confirmed, onMixFeedback }: Props): ReactElement {
  return (
    <div
      data-testid="segment-mix-list"
      aria-disabled={!confirmed}
      className={`border rounded p-4 ${!confirmed ? "cursor-not-allowed opacity-60" : ""}`}
    >
      <h3 className="text-sm font-medium mb-2">编号片段试听</h3>
      <div className="space-y-2">
        {segments.map((seg) => (
          <div key={seg.id} className="flex items-center gap-2 border-b pb-2">
            <span className="text-xs font-mono">#{seg.index}</span>
            <span className="text-xs flex-1">{seg.text}</span>
            <button
              aria-label="试听片段"
              className="px-2 py-1 text-xs border rounded"
              disabled={!confirmed}
              onClick={() => {
                const a = new Audio(seg.preview_url);
                a.play();
              }}
            >
              试听
            </button>
            <button
              aria-label="提交反馈"
              className="px-2 py-1 text-xs border rounded"
              disabled={!confirmed}
              onClick={() => onMixFeedback(seg.id)}
            >
              提交反馈
            </button>
          </div>
        ))}
      </div>
    </div>
  );
}
