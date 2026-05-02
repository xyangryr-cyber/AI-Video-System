import type { ReactElement } from "react";

export interface BgmCandidate {
  id: string;
  preview_url: string;
  raw_bgm_url: string;
  is_recommended: boolean;
  fit_review: { verdict: "PASS" | "FAIL"; checks: number };
}

interface Props {
  candidate: BgmCandidate;
  isSelected: boolean;
  onSelect: (candidate: BgmCandidate) => void;
}

export function Phase5CandidateCard({
  candidate,
  isSelected,
  onSelect,
}: Props): ReactElement {
  return (
    <article
      aria-pressed={isSelected}
      data-testid="p5-candidate-card"
      className={`border rounded p-3 ${isSelected ? "ring-2 ring-blue-500" : ""}`}
    >
      <div className="text-sm font-medium mb-2">
        {candidate.id}
        {candidate.is_recommended && (
          <span className="ml-2 text-xs text-blue-600">推荐</span>
        )}
      </div>

      <div className="flex gap-2 mb-2">
        <button
          aria-label="试听混音预览"
          className="px-2 py-1 text-xs border rounded"
          onClick={() => {
            const a = new Audio(candidate.preview_url);
            a.play();
          }}
        >
          试听
        </button>
        <button
          aria-label="试听原曲"
          className="px-2 py-1 text-xs border rounded"
          onClick={() => {
            const a = new Audio(candidate.raw_bgm_url);
            a.play();
          }}
        >
          原曲
        </button>
      </div>

      <div className="mb-2">
        {candidate.fit_review.verdict === "PASS" ? (
          <span data-testid="fit-pass" className="text-xs bg-green-100 text-green-700 px-1 rounded">
            PASS
          </span>
        ) : (
          <span data-testid="fit-fail" className="text-xs bg-red-100 text-red-700 px-1 rounded">
            FAIL
          </span>
        )}
      </div>

      <button
        aria-label="选定此候选"
        className="px-2 py-1 text-xs border rounded"
        onClick={(e) => {
          e.stopPropagation();
          onSelect(candidate);
        }}
      >
        选定
      </button>
    </article>
  );
}
