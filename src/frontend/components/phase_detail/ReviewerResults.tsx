import type { ReactElement } from "react";
import type { ReviewerResult } from "../PhaseDetailDrawer";

interface Props {
  results: ReviewerResult[] | null | undefined;
  readOnly: boolean;
}

export function ReviewerResults({ results, readOnly: _readOnly }: Props): ReactElement {
  if (!results || results.length === 0) {
    return (
      <div data-testid="block-reviewer-results" className="p-3 border rounded text-gray-500">
        No data — no reviewer results recorded.
      </div>
    );
  }
  return (
    <div data-testid="block-reviewer-results" className="p-3 border rounded">
      <h3 className="font-semibold mb-2">Reviewer Results</h3>
      <ul className="space-y-1">
        {results.map((r, i) => (
          <li key={i} className="text-sm">
            <span className="font-medium">{r.reviewer}</span>:{" "}
            <span className={r.verdict === "pass" ? "text-green-600" : "text-red-600"}>
              {r.verdict}
            </span>
            {r.notes && <span className="ml-1 text-gray-500">— {r.notes}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
