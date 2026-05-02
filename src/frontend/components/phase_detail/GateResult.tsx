import type { ReactElement } from "react";
import type { GateCheckResult } from "../PhaseDetailDrawer";

interface Props {
  results: GateCheckResult[] | null | undefined;
  readOnly: boolean;
}

export function GateResult({ results, readOnly: _readOnly }: Props): ReactElement {
  if (!results || results.length === 0) {
    return (
      <div data-testid="block-gate-result" className="p-3 border rounded text-gray-500">
        No data — no gate checks recorded.
      </div>
    );
  }
  return (
    <div data-testid="block-gate-result" className="p-3 border rounded">
      <h3 className="font-semibold mb-2">Gate Results</h3>
      <ul className="space-y-1">
        {results.map((g, i) => (
          <li key={i} className="text-sm">
            <span className={g.passed ? "text-green-600" : "text-red-600"}>
              {g.passed ? "[PASS]" : "[FAIL]"}
            </span>{" "}
            <span className="font-medium">{g.check_name}</span>
            {!g.passed && g.reason && <span className="ml-1 text-red-500">Reason: {g.reason}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}
